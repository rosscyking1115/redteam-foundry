"""The CHANGELOG heading a release ships with.

Defends: that the top-most versioned `CHANGELOG.md` heading agrees with the
version being published and with the day it is published on — the check
`.github/workflows/publish.yml` runs in its gate job, before anything is built.

Until now that heading was guarded by a tickbox in `docs/RELEASING.md` and
nothing else, while every other release constraint — the suite passing, the tag
matching the version, the commit being reachable from `main` — was enforced in
the workflow. `publish.yml`'s own header makes that argument about 0.4.0: safe
as a property of that release, not of the mechanism. The heading was in the same
position, and it had already gone wrong: the 0.5.0 heading was first stamped
with the working day while the calendar had rolled to the next date. A PyPI
description is frozen at upload, so a wrong date there is permanent.

The version half is asserted here against the *live* files as well, so a bump
that forgets the heading fails on the pull request rather than at the release.
The workflow keeps its own copy deliberately: a release must not depend on a
check reported elsewhere, possibly against a different commit.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]

_SPEC = importlib.util.spec_from_file_location(
    "check_release_heading", PROJECT_ROOT / "scripts" / "check_release_heading.py"
)
assert _SPEC and _SPEC.loader
crh = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = crh
_SPEC.loader.exec_module(crh)


# ---------------------------------------------------------------------------
# Parsing — including the two headings that must NOT be picked
# ---------------------------------------------------------------------------


def test_the_real_changelog_parses() -> None:
    """Non-vacuity: if the pattern stopped matching, everything below is hollow."""
    version, date = crh.top_heading((PROJECT_ROOT / "CHANGELOG.md").read_text(encoding="utf-8"))
    assert version.count(".") == 2, f"parsed version looks wrong: {version!r}"
    assert len(date) == 10 and date[4] == "-", f"parsed date looks wrong: {date!r}"


def test_unreleased_is_not_mistaken_for_a_version() -> None:
    """`## [Unreleased]` sits above every release heading and carries no date."""
    text = "## [Unreleased]\n\n## [0.5.0] — 2026-08-05\n\n## [0.4.1] — 2026-08-03\n"
    assert crh.top_heading(text) == ("0.5.0", "2026-08-05")


def test_a_heading_with_a_trailing_title_still_parses() -> None:
    """Older entries carry a title after the date; the top one might again."""
    text = "## [0.2.0] — 2026-07-02 — the adversarial benchmark foundry\n"
    assert crh.top_heading(text) == ("0.2.0", "2026-07-02")


def test_a_changelog_with_no_versioned_heading_raises_rather_than_passing() -> None:
    """ "Nothing to disagree with" must not read as agreement."""
    with pytest.raises(ValueError, match="no versioned heading found"):
        crh.top_heading("# Changelog\n\n## [Unreleased]\n")


# ---------------------------------------------------------------------------
# The timestamp — why the event payload and not the runner clock
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("stamp", "expected"),
    [
        ("2026-08-05T00:15:23Z", "2026-08-05"),
        ("2026-08-05T00:15:23+00:00", "2026-08-05"),
        # 23:30 in +05:30 is still the 4th in UTC. A runner in another region
        # reading its own clock would disagree with the release; this does not.
        ("2026-08-05T05:00:00+05:30", "2026-08-04"),
        ("2026-08-04T20:00:00-05:00", "2026-08-05"),
    ],
)
def test_published_date_is_utc_from_the_releases_own_timestamp(stamp: str, expected: str) -> None:
    assert crh.published_date(stamp) == expected


# ---------------------------------------------------------------------------
# The two assertions — each names WHICH field, with both values
# ---------------------------------------------------------------------------


def _problems(hv: str, hd: str, v: str, d: str) -> list[str]:
    return crh.problems(heading_version=hv, heading_date=hd, version=v, date=d)


def test_agreement_reports_nothing() -> None:
    assert _problems("0.5.0", "2026-08-05", "0.5.0", "2026-08-05") == []


def test_a_version_mismatch_names_the_field_and_both_values() -> None:
    (msg,) = _problems("0.5.0", "2026-08-05", "0.5.1", "2026-08-05")
    assert msg.startswith("VERSION mismatch")
    assert "'0.5.0'" in msg and "'0.5.1'" in msg


def test_a_date_mismatch_names_the_field_and_both_values() -> None:
    (msg,) = _problems("0.5.0", "2026-08-04", "0.5.0", "2026-08-05")
    assert msg.startswith("DATE mismatch")
    assert "'2026-08-04'" in msg and "'2026-08-05'" in msg


def test_both_wrong_reports_both_rather_than_stopping_at_the_first() -> None:
    """A gate that reports one of two defects sends you round the loop twice."""
    msgs = _problems("0.5.0", "2026-08-04", "0.5.1", "2026-08-09")
    assert len(msgs) == 2
    assert any(m.startswith("VERSION mismatch") for m in msgs)
    assert any(m.startswith("DATE mismatch") for m in msgs)


# ---------------------------------------------------------------------------
# The live files, so a forgotten heading fails on the PR and not at the release
# ---------------------------------------------------------------------------


def test_the_committed_heading_version_matches_pyproject() -> None:
    version, _ = crh.top_heading((PROJECT_ROOT / "CHANGELOG.md").read_text(encoding="utf-8"))
    declared = crh.declared_version()
    assert version == declared, (
        f"CHANGELOG.md's top heading is [{version}] but pyproject.toml declares {declared!r}. "
        "Bumping one without the other means the published notes describe a different "
        "version than the package."
    )
