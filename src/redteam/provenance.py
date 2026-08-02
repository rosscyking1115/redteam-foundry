"""Locale-provenance renderings of Chinese prompts, and divergence between them.

The question
------------
Published Chinese safety corpora reach Traditional-Chinese evaluation by
different routes: some are converted glyph-by-glyph from Simplified, some are
converted with a Taiwan vocabulary dictionary, some are written natively in
Taiwan Mandarin. This module produces those renderings from one source and
measures how far apart they are.

If the semantic content is identical and only the locale rendering differs,
then **any** downstream change in a guard classifier's verdict, an LLM judge's
verdict, or a model ranking is a measurement artefact by construction. That is
the construct-validity question this module exists to support.

Two arms
--------
``from_native``      A Taiwan-authored prompt is pushed down to Simplified and
                     brought back two ways. The native text is ground truth,
                     so all three renderings carry identical intent by
                     construction. This is the stronger arm.

``from_simplified``  A Simplified-authored prompt is converted up two ways.
                     There is no native rendering to compare against, so this
                     arm measures A-vs-B divergence only.

Why ``s2twp`` and not ``s2tw``
------------------------------
``s2tw`` adds only *TWVariants* — character-shape preferences such as 裏→裡.
``s2twp`` additionally applies *TWPhrases*, the PRC→Taiwan **vocabulary**
dictionary (內存→記憶體, 網絡→網路, 信息→資訊). Measured on vocabulary-bearing
prompts, ``s2tw`` reproduced ``s2t`` output on 4 of 5 items while ``s2twp``
differed on 5 of 5. Selecting ``s2tw`` as the dictionary condition would
therefore collapse it into the glyph-only condition and manufacture a null
result from a configuration choice. ``s2twp`` is the dictionary condition.

No prompt text is written to this repository. This module transforms text
supplied by the caller and reports metrics.
"""

from __future__ import annotations

import difflib
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:  # pragma: no cover - typing only
    from opencc import OpenCC as _OpenCC

# ---------------------------------------------------------------------------
# OpenCC configurations, recorded per rendering
# ---------------------------------------------------------------------------

Rendering = Literal["native", "simplified", "glyph_only", "dictionary_localised"]

#: OpenCC config used for each leg. Recorded alongside every result so a run
#: can be reproduced exactly, and so a future OpenCC release that changes a
#: dictionary is detectable rather than silent.
OPENCC_CONFIGS: dict[str, str] = {
    # native -> simplified. `tw2sp` applies TWPhrases in reverse, so the
    # simplified rendering looks like PRC-authored text rather than Taiwan
    # vocabulary wearing simplified glyphs.
    "down": "tw2sp",
    # simplified -> traditional, glyph mapping only.
    "glyph_only": "s2t",
    # simplified -> traditional, with the Taiwan vocabulary dictionary.
    "dictionary_localised": "s2twp",
}

#: Characters observed to survive a Traditional -> Simplified -> Traditional
#: round trip as a *different* character, because the downward leg is
#: many-to-one and the upward leg cannot recover which source character was
#: meant. Each pair is (native form, form produced by glyph-only conversion).
#:
#: This set is empirical, not exhaustive — it is what a 17-item TS-Bench
#: sample surfaced. `collapse_artefacts` detects the phenomenon generally by
#: checking whether two differing characters share a simplified form, so a
#: pair missing from this list is still counted. The list is documentation of
#: the effect, not the mechanism that finds it.
OBSERVED_COLLAPSE_PAIRS: tuple[tuple[str, str], ...] = (
    ("台", "臺"),
    ("吃", "喫"),
    ("才", "纔"),
    ("為", "爲"),
    ("裡", "裏"),
    ("並", "併"),
    ("煙", "菸"),
)

_CJK_START = "一"
_CJK_END = "鿿"


def _is_cjk(ch: str) -> bool:
    return _CJK_START <= ch <= _CJK_END


# ---------------------------------------------------------------------------
# Converter access
# ---------------------------------------------------------------------------

_CONVERTERS: dict[str, _OpenCC] = {}


def _converter(config: str) -> _OpenCC:
    """Return a cached OpenCC converter, or explain how to install it.

    OpenCC is an optional dependency (``pip install 'redteam-foundry[provenance]'``)
    because the rest of the corpus-audit path needs no native extension.
    """
    cached = _CONVERTERS.get(config)
    if cached is not None:
        return cached
    try:
        from opencc import OpenCC
    except ImportError as exc:  # pragma: no cover - exercised by install shape
        raise ImportError(
            "Locale-provenance renderings need OpenCC. "
            "Install with: pip install 'redteam-foundry[provenance]'"
        ) from exc
    converter = OpenCC(config)
    _CONVERTERS[config] = converter
    return converter


def convert(text: str, config: str) -> str:
    """Convert `text` using a named OpenCC config (e.g. ``s2t``, ``s2twp``)."""
    return str(_converter(config).convert(text))


# ---------------------------------------------------------------------------
# Divergence
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Divergence:
    """How far apart two renderings of the same intent are."""

    edit_distance: int
    length: int
    spans: tuple[tuple[str, str], ...]
    char_variant_subs: int
    vocabulary_subs: int
    collapse_artefacts: tuple[tuple[str, str], ...]

    @property
    def differs(self) -> bool:
        return self.edit_distance > 0

    @property
    def normalised(self) -> float:
        """Edit distance per character of the reference rendering."""
        return self.edit_distance / self.length if self.length else 0.0


def edit_distance(a: str, b: str) -> int:
    """Character-level Levenshtein distance."""
    if a == b:
        return 0
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        current = [i]
        for j, cb in enumerate(b, 1):
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (ca != cb)))
        previous = current
    return previous[-1]


def changed_spans(a: str, b: str) -> tuple[tuple[str, str], ...]:
    """Substituted spans between two renderings, as (from, to) pairs."""
    out: list[tuple[str, str]] = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b).get_opcodes():
        if tag != "equal":
            out.append((a[i1:i2], b[j1:j2]))
    return tuple(out)


def collapse_artefacts(reference: str, converted: str) -> tuple[tuple[str, str], ...]:
    """Character substitutions explained by many-to-one Traditional->Simplified.

    A pair counts when both characters are CJK, they differ, and they share a
    simplified form — i.e. the downward leg destroyed the distinction and the
    upward leg guessed. Distinct from vocabulary substitution, and reported
    separately because it is a round-trip artefact rather than a locale one.
    """
    out: list[tuple[str, str]] = []
    for src, dst in changed_spans(reference, converted):
        if len(src) != len(dst):
            continue
        for x, y in zip(src, dst, strict=True):
            if x == y or not (_is_cjk(x) and _is_cjk(y)):
                continue
            if convert(x, "t2s") == convert(y, "t2s"):
                out.append((x, y))
    return tuple(out)


def divergence(reference: str, other: str, *, detect_collapse: bool = True) -> Divergence:
    """Measure divergence of `other` from `reference`."""
    spans = changed_spans(reference, other)
    char_variant = sum(1 for s, d in spans if len(s) == 1 and len(d) == 1)
    return Divergence(
        edit_distance=edit_distance(reference, other),
        length=len(reference),
        spans=spans,
        char_variant_subs=char_variant,
        vocabulary_subs=len(spans) - char_variant,
        collapse_artefacts=(collapse_artefacts(reference, other) if detect_collapse else ()),
    )


# ---------------------------------------------------------------------------
# Rendering sets
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ProvenanceSet:
    """Three renderings of one semantic intent, plus how far apart they are.

    `native` is None on the forward arm, where no Taiwan-authored rendering
    exists to compare against.
    """

    item_id: str
    native: str | None
    simplified: str
    glyph_only: str
    dictionary_localised: str
    configs: dict[str, str]

    @property
    def glyph_vs_dictionary(self) -> Divergence:
        """A vs B — the comparison kill criterion 1 is stated against."""
        return divergence(self.glyph_only, self.dictionary_localised)

    @property
    def glyph_vs_native(self) -> Divergence | None:
        """A vs C. None on the forward arm."""
        if self.native is None:
            return None
        return divergence(self.native, self.glyph_only)

    @property
    def dictionary_vs_native(self) -> Divergence | None:
        """B vs C. None on the forward arm."""
        if self.native is None:
            return None
        return divergence(self.native, self.dictionary_localised)


def from_native(item_id: str, native: str) -> ProvenanceSet:
    """Round-trip arm: Taiwan-authored text down to Simplified and back twice.

    All three renderings carry identical semantic intent because they derive
    mechanically from one source, so no equivalence judgement is required.
    """
    simplified = convert(native, OPENCC_CONFIGS["down"])
    return ProvenanceSet(
        item_id=item_id,
        native=native,
        simplified=simplified,
        glyph_only=convert(simplified, OPENCC_CONFIGS["glyph_only"]),
        dictionary_localised=convert(simplified, OPENCC_CONFIGS["dictionary_localised"]),
        configs=dict(OPENCC_CONFIGS),
    )


def from_simplified(item_id: str, simplified: str) -> ProvenanceSet:
    """Forward arm: Simplified-authored text converted up two ways.

    No native rendering exists, so `glyph_vs_native` and `dictionary_vs_native`
    return None rather than a fabricated comparison.
    """
    return ProvenanceSet(
        item_id=item_id,
        native=None,
        simplified=simplified,
        glyph_only=convert(simplified, OPENCC_CONFIGS["glyph_only"]),
        dictionary_localised=convert(simplified, OPENCC_CONFIGS["dictionary_localised"]),
        configs={k: v for k, v in OPENCC_CONFIGS.items() if k != "down"},
    )


# ---------------------------------------------------------------------------
# Aggregate reporting
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class GateReport:
    """Corpus-level divergence summary — the 'is there an experiment' answer."""

    n_items: int
    n_chars: int
    glyph_differs_from_dictionary: int
    glyph_differs_from_native: int | None
    dictionary_differs_from_native: int | None
    mean_normalised_glyph_vs_dictionary: float
    # Substitution taxonomy, measured on the A-vs-B comparison.
    char_variant_subs: int
    vocabulary_subs: int
    # Collapse counts are comparison-specific and must say which comparison.
    # A-vs-B undercounts the effect badly: a character that both routes get
    # wrong the same way (台 -> 臺) is invisible there and only shows up
    # against native. Reporting one unlabelled `collapse_artefacts` number
    # invites quoting the smaller figure as if it were the degradation.
    collapse_glyph_vs_dictionary: int
    collapse_glyph_vs_native: int | None

    @property
    def glyph_vs_dictionary_rate(self) -> float:
        """Share of items where the two conversion routes disagree.

        Zero here means kill criterion 1 fires: the renderings are the same
        text, so there is nothing for a downstream verdict to differ on.
        """
        return self.glyph_differs_from_dictionary / self.n_items if self.n_items else 0.0


def gate_report(sets: list[ProvenanceSet]) -> GateReport:
    """Summarise divergence across a corpus.

    Returns zero counts for an empty input rather than raising — but note that
    every rate is then 0.0, which reads identically to 'the renderings are
    identical'. Callers must check `n_items` before interpreting a null result.
    """
    has_native = bool(sets) and all(s.native is not None for s in sets)
    ab = [s.glyph_vs_dictionary for s in sets]
    return GateReport(
        n_items=len(sets),
        n_chars=sum(len(s.native or s.simplified) for s in sets),
        glyph_differs_from_dictionary=sum(d.differs for d in ab),
        glyph_differs_from_native=(
            sum(1 for s in sets if (d := s.glyph_vs_native) is not None and d.differs)
            if has_native
            else None
        ),
        dictionary_differs_from_native=(
            sum(1 for s in sets if (d := s.dictionary_vs_native) is not None and d.differs)
            if has_native
            else None
        ),
        mean_normalised_glyph_vs_dictionary=(
            sum(d.normalised for d in ab) / len(ab) if ab else 0.0
        ),
        char_variant_subs=sum(d.char_variant_subs for d in ab),
        vocabulary_subs=sum(d.vocabulary_subs for d in ab),
        collapse_glyph_vs_dictionary=sum(len(d.collapse_artefacts) for d in ab),
        collapse_glyph_vs_native=(
            sum(len(d.collapse_artefacts) for s in sets if (d := s.glyph_vs_native) is not None)
            if has_native
            else None
        ),
    )
