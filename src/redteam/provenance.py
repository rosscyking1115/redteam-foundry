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
Read from the installed configs rather than assumed (see `redteam.opencc_pin`):

    s2t    = STPhrases, STCharacters
    s2tw   = STPhrases, STCharacters, TWVariantsPhrases, TWVariants
    s2twp  = STPhrases, STCharacters, TWPhrases, TWVariantsPhrases, TWVariants

``s2tw`` is **not** ``s2t``. It runs a genuine Taiwan character-variant stage —
裏→裡, 爲→為, 麪→麵 — and differs from ``s2t`` on any text containing those
forms. What it lacks is *TWPhrases*, the word-level PRC→Taiwan vocabulary
dictionary (內存→記憶體, 網絡→網路, 信息→資訊).

``s2twp`` is the dictionary condition because it is the only chain carrying
word-level vocabulary. ``s2tw`` is retained as an intermediate so the two
stages can be attributed separately (see `EditProfile`): the edits ``s2tw``
adds over ``s2t`` are Taiwan *variant* edits, and the edits ``s2twp`` adds
over ``s2tw`` are *TWPhrases* edits. Reporting one undifferentiated diff
invites the criticism that the whole effect is a handful of dictionary
lookups; the decomposition answers it with a number.

``s2twp`` is a partial vocabulary mapping, not comprehensive Taiwan
localisation — 775 TWPhrases entries against 4,800+ groups in Taiwan's
official cross-strait difference list.

The Hong Kong arm
-----------------
``s2hk`` = STPhrases, STCharacters, HKVariantsPhrases, HKVariants. It loads no
HKPhrases (only ``s2hkp`` does, and that file has 39 entries), so it introduces
no Cantonese morphology — no 嘅/咗/喺. Its output is mechanical Traditional
standard Chinese under Hong Kong glyph conventions: neither Taiwan text nor
real Hong Kong informal writing.

It exists to separate *Taiwan-specific* tuning from *Traditional-Chinese-general*
tuning in whatever consumes these renderings. Verdicts that move identically
for ``s2twp`` and ``s2hk`` indicate the latter.

No prompt text is written to this repository. This module transforms text
supplied by the caller and reports metrics.
"""

from __future__ import annotations

import difflib
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from redteam.opencc_pin import MULTI_TARGET_SOURCE_CHARS

if TYPE_CHECKING:  # pragma: no cover - typing only
    from opencc import OpenCC as _OpenCC

# ---------------------------------------------------------------------------
# OpenCC configurations, recorded per rendering
# ---------------------------------------------------------------------------

Rendering = Literal[
    "native",
    "simplified",
    "glyph_only",
    "variants_only",
    "dictionary_localised",
    "hong_kong",
]

#: OpenCC config used for each leg. Recorded alongside every result so a run
#: can be reproduced exactly, and so a future OpenCC release that changes a
#: dictionary is detectable rather than silent. Content pins for every
#: dictionary in these chains live in `redteam.opencc_pin`.
OPENCC_CONFIGS: dict[str, str] = {
    # native -> simplified. `tw2sp` applies TWPhrases in reverse, so the
    # simplified rendering looks like PRC-authored text rather than Taiwan
    # vocabulary wearing simplified glyphs.
    "down": "tw2sp",
    # A: character restoration only.
    "glyph_only": "s2t",
    # Intermediate, not a reported condition: character restoration plus the
    # Taiwan variant stage, without TWPhrases. Used to attribute edits between
    # the two stages rather than reporting one opaque diff.
    "variants_only": "s2tw",
    # B: character restoration + Taiwan variants + TWPhrases vocabulary.
    "dictionary_localised": "s2twp",
    # D: character restoration + Hong Kong variants. No HKPhrases, so no
    # Cantonese morphology is introduced.
    "hong_kong": "s2hk",
}

#: Conditions reported in the analysis. `variants_only` is deliberately absent:
#: it is a measurement instrument, not a rendering anyone would ship.
REPORTED_CONDITIONS: tuple[str, ...] = (
    "native",
    "glyph_only",
    "dictionary_localised",
    "hong_kong",
)

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
class EditProfile:
    """A triplet as a bundle of *measured* edits, not three opaque labels.

    Each conversion stage is attributed separately, so an effect can be traced
    to character restoration, to Taiwan variant preference, or to a TWPhrases
    vocabulary lookup — rather than reported as one undifferentiated diff.

    `ambiguity_opportunities` counts source characters that STCharacters maps
    to more than one traditional target. `ambiguity_correct` counts how many of
    those the glyph-only route resolved the way the native author wrote them.
    The native text is the gold standard here, which is what makes this
    machine-checkable without an annotator.
    """

    n_chars: int
    # Stage attribution, each measured against the previous stage's output.
    character_restoration_edits: int  # native -> A (STCharacters/STPhrases)
    taiwan_variant_edits: int  # A -> s2tw (TWVariants*)
    twphrases_edits: int  # s2tw -> B (TWPhrases)
    hong_kong_variant_edits: int  # A -> D (HKVariants*)
    # One-to-many restoration, scored against the native gold.
    ambiguity_opportunities: int
    ambiguity_scored: int
    ambiguity_correct: int

    @property
    def ambiguity_accuracy(self) -> float | None:
        """Share of *scorable* opportunities restored as the author wrote them.

        None when nothing was scorable — distinct from 0.0, which would mean
        every scorable opportunity was resolved wrongly. Callers must check for
        None rather than treating a missing rate as a passing one.
        """
        if not self.ambiguity_scored:
            return None
        return self.ambiguity_correct / self.ambiguity_scored


@dataclass(frozen=True, slots=True)
class ProvenanceSet:
    """Four renderings of one semantic intent, plus how far apart they are.

    `native` is None on the forward arm, where no Taiwan-authored rendering
    exists to compare against. `variants_only` is an instrument for edit
    attribution rather than a reported condition.
    """

    item_id: str
    native: str | None
    simplified: str
    glyph_only: str
    variants_only: str
    dictionary_localised: str
    hong_kong: str
    configs: dict[str, str]
    edits: EditProfile

    def rendering(self, condition: str) -> str:
        """Text for a named condition. Raises on an unknown name."""
        text = {
            "native": self.native,
            "simplified": self.simplified,
            "glyph_only": self.glyph_only,
            "variants_only": self.variants_only,
            "dictionary_localised": self.dictionary_localised,
            "hong_kong": self.hong_kong,
        }[condition]
        if text is None:
            raise ValueError(f"condition {condition!r} is absent on this arm")
        return text

    @property
    def native_vs_glyph(self) -> Divergence | None:
        """C vs A — the PRIMARY preregistered contrast. None on the forward arm."""
        if self.native is None:
            return None
        return divergence(self.native, self.glyph_only)

    @property
    def glyph_vs_dictionary(self) -> Divergence:
        """A vs B — mechanism probe: what TWPhrases plus variants buy."""
        return divergence(self.glyph_only, self.dictionary_localised)

    @property
    def glyph_vs_hong_kong(self) -> Divergence:
        """A vs D — mechanism probe: Taiwan-specific vs Traditional-general."""
        return divergence(self.glyph_only, self.hong_kong)

    @property
    def dictionary_vs_native(self) -> Divergence | None:
        """B vs C. None on the forward arm."""
        if self.native is None:
            return None
        return divergence(self.native, self.dictionary_localised)

    @property
    def hong_kong_vs_native(self) -> Divergence | None:
        """D vs C. None on the forward arm."""
        if self.native is None:
            return None
        return divergence(self.native, self.hong_kong)


def _ambiguity(simplified: str, glyph_only: str, native: str | None) -> tuple[int, int, int]:
    """One-to-many restoration opportunities, how many were scorable, how many matched.

    An *opportunity* is a source character STCharacters maps to more than one
    traditional target. Correctness is scored against the native text, which is
    the gold standard on the round-trip arm — so this needs no annotator.

    Scoring is per-position and therefore only valid when the three strings
    align character-for-character. A phrase rule that changes a span's length
    breaks that alignment, so those items are counted as opportunities but not
    as scorable, rather than being guessed at. On the forward arm there is no
    gold at all and nothing is scorable.

    Returns (opportunities, scorable, correct).
    """
    opportunities = sum(1 for ch in simplified if ch in MULTI_TARGET_SOURCE_CHARS)
    aligned = native is not None and len(simplified) == len(glyph_only) == len(native)
    if not aligned or native is None:
        return (opportunities, 0, 0)
    correct = sum(
        1
        for i, src in enumerate(simplified)
        if src in MULTI_TARGET_SOURCE_CHARS and glyph_only[i] == native[i]
    )
    return (opportunities, opportunities, correct)


def _profile(
    native: str | None,
    simplified: str,
    glyph_only: str,
    variants_only: str,
    dictionary_localised: str,
    hong_kong: str,
) -> EditProfile:
    opportunities, scored, correct = _ambiguity(simplified, glyph_only, native)
    return EditProfile(
        n_chars=len(native or simplified),
        character_restoration_edits=(
            edit_distance(native, glyph_only) if native is not None else 0
        ),
        taiwan_variant_edits=edit_distance(glyph_only, variants_only),
        twphrases_edits=edit_distance(variants_only, dictionary_localised),
        hong_kong_variant_edits=edit_distance(glyph_only, hong_kong),
        ambiguity_opportunities=opportunities,
        ambiguity_scored=scored,
        ambiguity_correct=correct,
    )


def _render(simplified: str) -> dict[str, str]:
    return {
        key: convert(simplified, OPENCC_CONFIGS[key])
        for key in ("glyph_only", "variants_only", "dictionary_localised", "hong_kong")
    }


def from_native(item_id: str, native: str) -> ProvenanceSet:
    """Round-trip arm: Taiwan-authored text down to Simplified and back.

    All renderings carry identical semantic intent because they derive
    mechanically from one source, so no equivalence judgement is required to
    establish comparability.
    """
    simplified = convert(native, OPENCC_CONFIGS["down"])
    r = _render(simplified)
    return ProvenanceSet(
        item_id=item_id,
        native=native,
        simplified=simplified,
        configs=dict(OPENCC_CONFIGS),
        edits=_profile(native, simplified, **r),
        **r,
    )


def from_simplified(item_id: str, simplified: str) -> ProvenanceSet:
    """Forward arm: Simplified-authored text converted up.

    No native rendering exists, so the `*_vs_native` comparisons return None
    rather than a fabricated one, and ambiguity correctness is not scored
    because there is no gold to score against.
    """
    r = _render(simplified)
    return ProvenanceSet(
        item_id=item_id,
        native=None,
        simplified=simplified,
        configs={k: v for k, v in OPENCC_CONFIGS.items() if k != "down"},
        edits=_profile(None, simplified, **r),
        **r,
    )


# ---------------------------------------------------------------------------
# Aggregate reporting
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class GateReport:
    """Corpus-level divergence summary — the 'is there an experiment' answer.

    The PRIMARY contrast is native vs glyph-only (C vs A). B and D are
    mechanism probes and are reported separately rather than symmetrically, so
    the analysis cannot be read as three interchangeable labels.
    """

    n_items: int
    n_chars: int
    # Primary contrast.
    native_differs_from_glyph: int | None
    # Mechanism probes.
    glyph_differs_from_dictionary: int
    glyph_differs_from_hong_kong: int
    dictionary_differs_from_native: int | None
    hong_kong_differs_from_native: int | None
    # Stage attribution, summed over the corpus. If the whole effect lives in
    # `twphrases_edits`, kill criterion 2 is live and must be reported.
    character_restoration_edits: int
    taiwan_variant_edits: int
    twphrases_edits: int
    hong_kong_variant_edits: int
    # One-to-many restoration against the native gold.
    ambiguity_opportunities: int
    ambiguity_scored: int
    ambiguity_correct: int
    # Items whose renderings are all identical, or differ only in 台/臺 —
    # the audit's kill criterion 3.
    items_all_identical: int
    items_differing_only_by_tai: int

    @property
    def native_vs_glyph_rate(self) -> float:
        """Primary divergence rate. Zero means there is nothing to measure."""
        if not self.n_items or self.native_differs_from_glyph is None:
            return 0.0
        return self.native_differs_from_glyph / self.n_items

    @property
    def ambiguity_accuracy(self) -> float | None:
        """Corpus-level one-to-many restoration accuracy, or None if unscored."""
        if not self.ambiguity_scored:
            return None
        return self.ambiguity_correct / self.ambiguity_scored

    @property
    def trivial_item_rate(self) -> float:
        """Share of items that are identical or differ only in 台/臺.

        The audit's kill criterion 3. A high value means the corpus carries too
        few locale-bearing opportunities for the contrast to be about locale.
        """
        if not self.n_items:
            return 0.0
        return (self.items_all_identical + self.items_differing_only_by_tai) / self.n_items


def _only_tai(s: ProvenanceSet) -> bool:
    """True when every difference from native is the 台/臺 substitution."""
    if s.native is None:
        return False
    for other in (s.glyph_only, s.dictionary_localised, s.hong_kong):
        for src, dst in changed_spans(s.native, other):
            if set(src) - {"台", "臺"} or set(dst) - {"台", "臺"}:
                return False
    return True


def gate_report(sets: list[ProvenanceSet]) -> GateReport:
    """Summarise divergence across a corpus.

    Returns zero counts for an empty input rather than raising — but every rate
    is then 0.0, which reads identically to 'the renderings are identical'.
    Callers must check `n_items` before interpreting a null result.
    """
    has_native = bool(sets) and all(s.native is not None for s in sets)

    def native_diffs(attr: str) -> int | None:
        if not has_native:
            return None
        return sum(1 for s in sets if (d := getattr(s, attr)) is not None and d.differs)

    identical = sum(
        1
        for s in sets
        if s.native is not None
        and s.native == s.glyph_only == s.dictionary_localised == s.hong_kong
    )
    return GateReport(
        n_items=len(sets),
        n_chars=sum(len(s.native or s.simplified) for s in sets),
        native_differs_from_glyph=native_diffs("native_vs_glyph"),
        glyph_differs_from_dictionary=sum(s.glyph_vs_dictionary.differs for s in sets),
        glyph_differs_from_hong_kong=sum(s.glyph_vs_hong_kong.differs for s in sets),
        dictionary_differs_from_native=native_diffs("dictionary_vs_native"),
        hong_kong_differs_from_native=native_diffs("hong_kong_vs_native"),
        character_restoration_edits=sum(s.edits.character_restoration_edits for s in sets),
        taiwan_variant_edits=sum(s.edits.taiwan_variant_edits for s in sets),
        twphrases_edits=sum(s.edits.twphrases_edits for s in sets),
        hong_kong_variant_edits=sum(s.edits.hong_kong_variant_edits for s in sets),
        ambiguity_opportunities=sum(s.edits.ambiguity_opportunities for s in sets),
        ambiguity_scored=sum(s.edits.ambiguity_scored for s in sets),
        ambiguity_correct=sum(s.edits.ambiguity_correct for s in sets),
        items_all_identical=identical,
        items_differing_only_by_tai=sum(1 for s in sets if _only_tai(s)) - identical,
    )
