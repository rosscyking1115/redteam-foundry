"""`tests/README.md` claims to index every suite. This makes that true.

Defends: the completeness claim in `tests/README.md` — that the index maps
*each* test suite to the claim it defends.

The claim was there for a long time with nothing behind it, and it was false —
every publication-surface suite and both live-smoke suites had no row. That is
this repository's attestation-is-not-enforcement finding landing in its own test
documentation: a statement about coverage, prominent and load-bearing in how a
reviewer reads the suite, and unfalsifiable because nothing compared it to the
directory. (No count is written here on purpose; a number describing a gap goes
stale the moment the gap is closed, which is the defect the absence catalogue's
own section headings had.)

The failure mode is quiet in the direction that matters. Adding a test file is
routine; adding the row is the step that gets forgotten, and forgetting it makes
the index *silently* less complete rather than visibly so. A reviewer who trusts
the index then concludes a claim is undefended when it is merely unlisted, or —
worse — sees a short index and believes the suite is small.

Two directions are checked, because either alone is satisfiable by a mistake:

* every test file has a row (the completeness claim itself);
* every row names a file that exists (so the index cannot rot into pointing at
  deleted suites, which would inflate apparent coverage).

Non-vacuity is asserted first. A regex that matched nothing would report "no
missing rows" and pass, which is the exact defect this file exists to stop.
"""

from __future__ import annotations

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TESTS_DIR = PROJECT_ROOT / "tests"
INDEX = TESTS_DIR / "README.md"

# Rows look like: | [`test_x.py`](unit/test_x.py) | what it defends |
# The link target is matched, not the label, so a row whose label and target
# disagree is caught by the "every row names a real file" direction below.
ROW_TARGET = re.compile(r"\]\(\s*((?:unit|smoke)/test_[A-Za-z0-9_]+\.py)\s*\)")

# Files that are infrastructure rather than suites: they defend no claim of
# their own, so a row for them would be noise. Named explicitly rather than
# pattern-matched, so adding a real suite can never be silently absorbed.
NOT_A_SUITE: frozenset[str] = frozenset(
    {
        "tests/conftest.py",
        "tests/__init__.py",
        "tests/unit/__init__.py",
        "tests/smoke/__init__.py",
    }
)


def _test_files() -> set[str]:
    """Every `test_*.py` under tests/, as a posix path relative to tests/."""
    return {
        p.relative_to(TESTS_DIR).as_posix()
        for p in TESTS_DIR.rglob("test_*.py")
        if f"tests/{p.relative_to(TESTS_DIR).as_posix()}" not in NOT_A_SUITE
    }


def _indexed() -> set[str]:
    return set(ROW_TARGET.findall(INDEX.read_text(encoding="utf-8")))


# ---------------------------------------------------------------------------
# Non-vacuity — this has to be able to fail before its passes mean anything
# ---------------------------------------------------------------------------


def test_the_scan_actually_finds_test_files() -> None:
    files = _test_files()
    assert len(files) >= 30, f"only {len(files)} test files discovered — the glob looks broken"


def test_the_scan_actually_finds_rows() -> None:
    rows = _indexed()
    assert len(rows) >= 30, (
        f"only {len(rows)} rows parsed from the index — the pattern looks broken"
    )


# ---------------------------------------------------------------------------
# The completeness claim, both directions
# ---------------------------------------------------------------------------


def test_every_suite_has_a_row() -> None:
    missing = sorted(_test_files() - _indexed())
    assert missing == [], (
        f"{len(missing)} test suite(s) absent from tests/README.md: {missing}. "
        "The index states it maps every suite; add a row naming the claim each one "
        "defends, or the claim is an attestation again."
    )


def test_every_row_names_a_suite_that_exists() -> None:
    stale = sorted(_indexed() - _test_files())
    assert stale == [], (
        f"{len(stale)} row(s) in tests/README.md point at files that do not exist: {stale}. "
        "A row for a deleted suite overstates what the suite covers."
    )


def test_smoke_suites_are_indexed_too() -> None:
    """The missing suites were all outside `tests/unit/`-shaped habit.

    Pinned by directory rather than by name: the gap was not one forgotten file
    but a whole class of them — publication-surface and smoke suites — so the
    check that matters is that no directory under tests/ is exempt. Smoke suites
    never run in CI, which is exactly why they are the ones to drop off an index
    maintained by hand.
    """
    smoke = {f for f in _test_files() if f.startswith("smoke/")}
    assert smoke, "no smoke suites found — this check would be vacuous"
    assert smoke <= _indexed(), f"unindexed smoke suites: {sorted(smoke - _indexed())}"
