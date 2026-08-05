"""Verify the top-most versioned CHANGELOG heading against the release itself.

The release path already refuses a tag whose name disagrees with the package
version, and refuses a commit that is not reachable from `main`. The CHANGELOG
heading — the version *and* the date a reader sees on PyPI — was guarded by a
tickbox in `docs/RELEASING.md` and nothing else.

That is the position `publish.yml`'s own header describes for 0.4.0: safe as a
property of that release rather than of the mechanism. It is not hypothetical
here. The 0.5.0 heading was first stamped `2026-08-04`, the working day, while
the calendar had already rolled to the 5th — and a PyPI description is frozen at
upload, so a wrong date there is permanent.

Two assertions, run in the gate job before anything is built or uploaded:

1. The heading's **version** equals the version in `pyproject.toml`.
2. The heading's **date** equals the date of the release's own
   `published_at` timestamp.

`published_at` is used rather than the runner's clock deliberately. It is the
release's own timestamp in UTC, so there is no timezone slop between whoever
clicks publish and whichever region the runner starts in, and no case where a
job crossing midnight disagrees with the release it is publishing.

    python scripts/check_release_heading.py --published-at 2026-08-05T00:15:23Z

Exit code is the signal. Do not pipe this into anything whose status you then
read — see finding #9.
"""

from __future__ import annotations

import argparse
import re
import tomllib
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHANGELOG = ROOT / "CHANGELOG.md"
PYPROJECT = ROOT / "pyproject.toml"

# `## [0.5.0] — 2026-08-05`, and also `## [0.2.0] — 2026-07-02 — some title`.
# `## [Unreleased]` carries no version digits and is skipped by construction,
# which is the point: the top-most *versioned* heading is the one that ships.
#
# The separator is an em dash in every heading this file has ever had — checked,
# not assumed — so the class is em dash or plain hyphen and nothing else. An en
# dash was considered and dropped: it appears nowhere, and the two are
# near-indistinguishable in most fonts, so accepting both would let a heading
# that looks right to a reviewer differ from every other one in the file.
HEADING = re.compile(
    r"^##\s*\[(?P<version>\d+\.\d+\.\d+)\]\s*[—\-]\s*(?P<date>\d{4}-\d{2}-\d{2})",
    re.MULTILINE,
)


def declared_version() -> str:
    return str(tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]["version"])


def top_heading(text: str) -> tuple[str, str]:
    """(version, date) of the first versioned heading. Raises if there is none.

    A file with no versioned heading must not read as "nothing to disagree
    with" — that is the same shape as every absence this project catalogues.
    """
    match = HEADING.search(text)
    if match is None:
        raise ValueError(
            "no versioned heading found in CHANGELOG.md. Expected a line like "
            "'## [X.Y.Z] — YYYY-MM-DD'; without one there is nothing to check and "
            "this gate would pass vacuously."
        )
    return match.group("version"), match.group("date")


def published_date(published_at: str) -> str:
    """`YYYY-MM-DD` in UTC from a GitHub release `published_at` timestamp."""
    stamp = datetime.fromisoformat(published_at.strip())
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=UTC)
    return stamp.astimezone(UTC).date().isoformat()


def problems(*, heading_version: str, heading_date: str, version: str, date: str) -> list[str]:
    """Every mismatch, each naming which field and both values."""
    found: list[str] = []
    if heading_version != version:
        found.append(
            f"VERSION mismatch: CHANGELOG.md's top heading says {heading_version!r} but "
            f"pyproject.toml declares {version!r}. The release notes would describe a "
            "different version than the one being published."
        )
    if heading_date != date:
        found.append(
            f"DATE mismatch: CHANGELOG.md's top heading says {heading_date!r} but the "
            f"release was published on {date!r} (UTC, from the release's own "
            "published_at). A PyPI description is frozen at upload, so a wrong date "
            "there is permanent."
        )
    return found


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--published-at",
        required=True,
        help="the release's published_at timestamp, e.g. 2026-08-05T00:15:23Z",
    )
    args = ap.parse_args()

    version = declared_version()
    try:
        heading_version, heading_date = top_heading(CHANGELOG.read_text(encoding="utf-8"))
    except ValueError as exc:
        print(f"FAIL: {exc}")
        return 1

    try:
        date = published_date(args.published_at)
    except ValueError as exc:
        print(f"FAIL: could not parse --published-at {args.published_at!r}: {exc}")
        return 1

    found = problems(
        heading_version=heading_version, heading_date=heading_date, version=version, date=date
    )
    if found:
        for line in found:
            print(f"FAIL: {line}")
        return 1

    print(f"ok: CHANGELOG heading [{heading_version}] — {heading_date} matches the release.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
