"""The headline figure's caption is a published claim, and is checked like one.

Defends: that the caption rendered into `docs/results_matrix.png` makes no
judge-agreement claim -- in particular not the `κ = 1.00, all 12 cells` that
0.4.0 retracted (METHODOLOGY section 7).

`docs/results_matrix.png` is embedded in `README.md`, which is also this
project's `long_description` — so its caption is rendered on the GitHub page and
on the PyPI project page, and travels intact into any screenshot of the figure.

It carried this until it was corrected:

    Point = LLM-judge ASR; whisker = 95% bootstrap CI;
    two-judge cross-validated (ASR κ = 1.00, all 12 cells).

0.4.0 retracted that exact claim. In 11 of the 12 cells both judges labelled
every case identically and constantly, so expected agreement `pe == 1` and
Cohen's κ is an undefined `0/0` that the scorer fills in as +1.000 by
convention. The figure was advertising as cross-validation the one claim the
repository had published a correction against, and it went on doing so through
two releases: the figure was checked three times during release work, and every
check confirmed the image *loaded*. None read what it said.

So the rule this module enforces is not "no false κ" but the stronger one that
falls out of where a caption lives:

**No judge-agreement claim belongs in this caption at all.** Every such figure
in this project needs a sentence of qualification to be read correctly — the
degenerate cells, the sample size, which cell the number came from — and a
caption is the one part of a document guaranteed to travel separated from its
qualification. That includes the *surviving* measurement, the positive
control's κ = +0.935 (n = 98): true, but attached to a cell that is not among
the 12 plotted, so in this caption it would read as though the matrix had been
validated at 0.935. The qualified version lives in `README.md` and
`METHODOLOGY.md` §7/§8, where the caveat travels with it.

Two sources are read, because either alone passes on a defect:

* **`scripts/plot_results.py`** — the caption lives in code, so editing only the
  PNG would leave the generator emitting the old text on its next run.
* **`docs/results_matrix.png`** — the generator records the caption in the PNG's
  `Description` metadata, so the *committed artifact* is checked too, not merely
  the code that ought to have produced it. The two must agree, which is what
  fails if the caption is edited and the figure is not regenerated.

What this does not do is read the pixels. A PNG whose `Description` disagrees
with the text rendered into it would pass, and OCR is not a cheap dependency to
take for that. The gap is narrow — both artifacts come from one constant on one
run — and it is stated rather than papered over.
"""

from __future__ import annotations

import re
import struct
import zlib
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
GENERATOR = PROJECT_ROOT / "scripts" / "plot_results.py"
FIGURE = PROJECT_ROOT / "docs" / "results_matrix.png"

# The generator is read as text rather than imported: it imports matplotlib at
# module scope, a dev-only dependency, and a guard that turns into a skip when a
# dependency is missing is the absence failure this repository keeps finding.
CAPTION_ASSIGNMENT = re.compile(r'^CAPTION\s*=\s*"([^"]*)"\s*$', re.MULTILINE)

# The caption the retraction was written about. Kept verbatim so the patterns
# below are tested against the real defect and not against a paraphrase of it.
RETRACTED_CAPTION = (
    "Point = LLM-judge ASR; whisker = 95% bootstrap CI; "
    "two-judge cross-validated (ASR κ = 1.00, all 12 cells)."
)

# Named separately from the blanket rule so the failure message tells whoever
# hits it which specific retraction they have just walked back into.
KAPPA_OF_ONE = re.compile(r"(?:κ|kappa)\s*[=:]?\s*\+?\s*1(?:[.,]0+)?(?!\d)", re.IGNORECASE)

# The blanket rule: no judge-agreement vocabulary in the caption, whatever the
# number attached to it. Deliberately scoped to this one caption — the same
# words are correct and wanted in README.md and METHODOLOGY.md, which have room
# for the caveat.
AGREEMENT_VOCABULARY = re.compile(
    r"κ|kappa|cross-?valid|cross-?judg|inter-?judge|inter-?rater|two-?judge|judges?\s+agree",
    re.IGNORECASE,
)


def _caption_from_source() -> str:
    matches = CAPTION_ASSIGNMENT.findall(GENERATOR.read_text(encoding="utf-8"))
    assert len(matches) == 1, (
        f"expected exactly one top-level CAPTION assignment in "
        f"{GENERATOR.relative_to(PROJECT_ROOT)}, found {len(matches)}. The caption must stay a "
        "single named constant, or this guard reads something other than what the figure says."
    )
    return matches[0]


def _png_text_chunks(path: Path) -> dict[str, str]:
    """Return the PNG's textual keyword -> value map, using only the stdlib.

    All three text chunk types are handled, and `iTXt` is the one that matters:
    a writer emits `tEXt` only while the value is Latin-1 encodable and switches
    to UTF-8 `iTXt` as soon as it is not. A caption containing `κ` lands in
    `iTXt` — so a reader that skipped it would report the retracted caption as
    *unreadable* rather than reject it, which is the wrong failure for the one
    string this guard most needs to catch.
    """
    raw = path.read_bytes()
    assert raw[:8] == b"\x89PNG\r\n\x1a\n", f"{path.name} is not a PNG"
    chunks: dict[str, str] = {}
    offset = 8
    while offset < len(raw):
        (length,) = struct.unpack(">I", raw[offset : offset + 4])
        kind = raw[offset + 4 : offset + 8]
        body = raw[offset + 8 : offset + 8 + length]
        if kind == b"tEXt":
            key, _, value = body.partition(b"\x00")
            chunks[key.decode("latin-1")] = value.decode("latin-1")
        elif kind == b"zTXt":
            key, _, rest = body.partition(b"\x00")
            chunks[key.decode("latin-1")] = zlib.decompress(rest[1:]).decode("latin-1")
        elif kind == b"iTXt":
            # keyword \0 compression_flag compression_method language \0 translated \0 text
            key, _, rest = body.partition(b"\x00")
            compressed = rest[0] == 1
            _, _, rest = rest[2:].partition(b"\x00")  # drop the language tag
            _, _, text = rest.partition(b"\x00")  # drop the translated keyword
            payload = zlib.decompress(text) if compressed else text
            chunks[key.decode("latin-1")] = payload.decode("utf-8")
        if kind == b"IEND":
            break
        offset += 12 + length
    return chunks


def _caption_from_figure() -> str:
    chunks = _png_text_chunks(FIGURE)
    assert "Description" in chunks, (
        f"{FIGURE.relative_to(PROJECT_ROOT)} carries no Description metadata. Regenerate it with "
        "`python scripts/plot_results.py`; a figure with no recorded caption cannot be checked, "
        "and an unreadable caption must not read as a clean one."
    )
    return chunks["Description"]


# ---------------------------------------------------------------------------
# Meta-tests: the guard has to be able to fail before its passes mean anything
# ---------------------------------------------------------------------------


def _synthetic_png(chunks: list[tuple[bytes, bytes]]) -> bytes:
    """Assemble a PNG made only of the given chunks, for exercising the reader."""
    out = b"\x89PNG\r\n\x1a\n"
    for kind, body in [*chunks, (b"IEND", b"")]:
        out += struct.pack(">I", len(body)) + kind + body
        out += struct.pack(">I", zlib.crc32(kind + body))
    return out


@pytest.mark.parametrize("compressed", [False, True])
def test_the_reader_handles_the_utf8_chunk_type(tmp_path: Path, compressed: bool) -> None:
    """The `iTXt` branch is only reachable via a non-ASCII caption.

    That is precisely the retracted caption, so an untested branch here would
    rot unnoticed until the one moment it is needed — and then downgrade a
    rejection into an "unreadable metadata" error.
    """
    text = "ASR κ = 1.00, all 12 cells".encode()
    payload = zlib.compress(text) if compressed else text
    body = b"Description\x00" + bytes([int(compressed), 0]) + b"\x00" + b"\x00" + payload
    png = tmp_path / "synthetic.png"
    png.write_bytes(_synthetic_png([(b"iTXt", body)]))

    assert _png_text_chunks(png)["Description"] == "ASR κ = 1.00, all 12 cells"


def test_the_caption_is_actually_found_and_says_something() -> None:
    """A guard that reads an empty string passes every assertion below it."""
    caption = _caption_from_source()
    assert len(caption) >= 30, f"caption looks empty or truncated: {caption!r}"
    assert "ASR" in caption, f"caption no longer names what is plotted: {caption!r}"


@pytest.mark.parametrize("pattern", [KAPPA_OF_ONE, AGREEMENT_VOCABULARY])
def test_the_patterns_match_the_caption_that_was_retracted(pattern: re.Pattern[str]) -> None:
    """Proves the guard bites, against the real defect rather than a mock of it.

    Without this, both patterns could be quietly edited into something that
    matches nothing and every test below would still pass.
    """
    assert pattern.search(RETRACTED_CAPTION), (
        f"{pattern.pattern!r} does not match the caption this guard exists to reject. "
        "The pattern has stopped working."
    )


@pytest.mark.parametrize(
    "wording",
    [
        "ASR κ = 1.00, all 12 cells",
        "kappa = 1.000",
        "κ=+1",
        "Cohen's kappa: 1.0",
        "two-judge cross-validated",
        "the judges agree",
        "inter-rater κ = +0.935",
    ],
)
def test_the_patterns_match_the_ways_the_claim_could_come_back(wording: str) -> None:
    """The defect returning in a different formatting is the same defect."""
    assert KAPPA_OF_ONE.search(wording) or AGREEMENT_VOCABULARY.search(wording), (
        f"{wording!r} would slip past both patterns"
    )


def test_the_patterns_do_not_reject_the_honest_caption() -> None:
    """A rule broad enough to fail a correct caption gets disabled, not obeyed."""
    honest = "Point = LLM-judge ASR; whisker = 95% bootstrap CI."
    assert not KAPPA_OF_ONE.search(honest)
    assert not AGREEMENT_VOCABULARY.search(honest)


# ---------------------------------------------------------------------------
# The guard itself
# ---------------------------------------------------------------------------


def test_the_caption_does_not_state_the_retracted_kappa() -> None:
    caption = _caption_from_source()
    hit = KAPPA_OF_ONE.search(caption)
    assert hit is None, (
        f"the figure caption states a κ of 1 ({hit.group(0)!r} in {caption!r}). 0.4.0 retracted "
        "that claim: 11 of the 12 cells' κ is an undefined 0/0 filled in as +1.000 by convention, "
        "not measured agreement. See CHANGELOG.md § Retracted."
    )


def test_the_caption_makes_no_judge_agreement_claim() -> None:
    caption = _caption_from_source()
    hit = AGREEMENT_VOCABULARY.search(caption)
    assert hit is None, (
        f"the figure caption makes a judge-agreement claim ({hit.group(0)!r} in {caption!r}). "
        "Every such figure here needs a sentence of qualification, and a caption travels "
        "separated from its qualification — a screenshot carries the caption and nothing else. "
        "Put it in README.md § 'Why the result is trustworthy, not just low' instead."
    )


def test_the_committed_figure_carries_the_caption_the_generator_would_draw() -> None:
    """Catches the caption being corrected in code without regenerating the PNG.

    That staleness is not cosmetic: the README's image URL is pinned to `main`
    on raw.githubusercontent.com, so the committed PNG — not the generator — is
    what GitHub and PyPI serve.
    """
    assert _caption_from_figure() == _caption_from_source(), (
        f"{FIGURE.relative_to(PROJECT_ROOT)} was rendered from a different caption than the one "
        f"in {GENERATOR.relative_to(PROJECT_ROOT)}. Regenerate: `python scripts/plot_results.py`."
    )


def test_the_committed_figure_itself_makes_no_retracted_claim() -> None:
    """The artifact is checked directly, not only the code that should produce it."""
    caption = _caption_from_figure()
    assert KAPPA_OF_ONE.search(caption) is None, f"published figure states a κ of 1: {caption!r}"
    assert AGREEMENT_VOCABULARY.search(caption) is None, (
        f"published figure makes a judge-agreement claim: {caption!r}"
    )
