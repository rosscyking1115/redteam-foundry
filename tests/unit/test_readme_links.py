"""No link in README.md may be relative.

`README.md` is this project's `long_description`, so PyPI renders it verbatim on
the project page. PyPI resolves *no* relative target: a link written `./LICENSE`
becomes a dead link there, and an image written `docs/results_matrix.png` renders
as a broken-image icon. GitHub resolves both, which is why the defect is
invisible in the place the file is usually read.

Two of the targets here make the point that this is not cosmetic:

* **`./LICENSE` is badge-wrapped** — `[![License: MIT](shields.io/...)](./LICENSE)`.
  A scan that reads only the outermost link of each line, or that eyeballs for
  `](./`, sees the shields.io URL and reports the line as absolute. This module
  matches on `](target)` instead, so it sees every target in a nested construct.
* **`docs/results_matrix.png` is the headline figure.** On PyPI the README is the
  entire delivery surface for the finding, so a broken image there is a missing
  piece of evidence rather than a layout blemish.

Images must use `raw.githubusercontent.com`: `github.com/.../blob/...` serves an
HTML page, so an `<img>` pointing at it renders broken on PyPI too.
"""

from __future__ import annotations

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
README = PROJECT_ROOT / "README.md"

# Matches the target of every inline link AND every inline image, including one
# nested inside the other — the badge case.
TARGET = re.compile(r"\]\(\s*([^)\s]+)")
ABSOLUTE = re.compile(r"^(https?://|mailto:)")
IMAGE_TARGET = re.compile(r"!\[[^\]]*\]\(\s*([^)\s]+)")
IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp")

RAW_HOST = "https://raw.githubusercontent.com/"
# The figure the finding is delivered through, named rather than pattern-matched:
# a filter over "images that look like figures" also catches the CI status badge.
HEADLINE_FIGURE = "docs/results_matrix.png"


def _targets() -> list[str]:
    return TARGET.findall(README.read_text(encoding="utf-8"))


def test_the_scan_actually_sees_targets() -> None:
    """A regex that matches nothing would pass every test below.

    It is also the specific way this check could silently stop working: the
    README is edited into a form the pattern no longer matches, and an empty
    result set reads as "no relative links".
    """
    targets = _targets()
    assert len(targets) >= 20, f"only {len(targets)} link targets found — the scan looks broken"


def test_the_scan_sees_badge_wrapped_targets() -> None:
    """Pins the property that motivates the pattern, not just the pattern.

    `./LICENSE` was badge-wrapped and would be missed by an outermost-link scan.
    """
    line = next(ln for ln in README.read_text(encoding="utf-8").splitlines() if "License-MIT" in ln)
    assert len(TARGET.findall(line)) == 2, (
        "the badge line should yield two targets — the shield image and the link it "
        "wraps. Seeing one means the scan reads only the outer or inner construct."
    )


def test_no_relative_links_survive() -> None:
    relative = sorted({t for t in _targets() if not ABSOLUTE.match(t) and not t.startswith("#")})
    assert relative == [], (
        f"{len(relative)} relative target(s) in README.md: {relative}. PyPI renders this "
        "file as the project description and resolves none of them, so each is a dead "
        "link or a broken image on the published page."
    )


def test_repository_file_images_are_served_from_raw_not_blob() -> None:
    """`github.com/.../blob/...` returns an HTML page, so an <img> renders broken.

    Scoped to `blob/` deliberately. Plenty of legitimate image sources live on
    github.com without being repository file views — the CI status badge is
    `github.com/<owner>/<repo>/actions/workflows/ci.yml/badge.svg`, an endpoint
    that really does serve an SVG. A rule of "no github.com images" would fail
    that correct line, so the rule names the actual defect instead.
    """
    for target in IMAGE_TARGET.findall(README.read_text(encoding="utf-8")):
        if "github.com/" in target and "/blob/" in target:
            assert target.startswith(RAW_HOST), (
                f"image target {target!r} is a GitHub file *page*, not the file. Use "
                f"{RAW_HOST}<owner>/<repo>/main/<path> instead."
            )


def test_the_headline_figure_is_a_raw_url() -> None:
    """The figure PyPI needs, pinned by name rather than by rule.

    The rule above is satisfied vacuously by a README containing no images at
    all, and this project's finding is delivered through that one image.
    """
    images = IMAGE_TARGET.findall(README.read_text(encoding="utf-8"))
    figures = [t for t in images if HEADLINE_FIGURE in t]
    assert figures, f"{HEADLINE_FIGURE} is missing from README.md"
    for target in figures:
        assert target.startswith(RAW_HOST), f"figure {target!r} will not render on PyPI"
        rel = target.split("/main/", 1)[1]
        assert (PROJECT_ROOT / rel).exists(), f"{rel} is linked but absent from the repository"


def test_every_github_link_points_at_a_file_in_this_repository() -> None:
    """Absolute is not the same as correct — a typo'd path 404s on both hosts."""
    prefixes = (
        "https://github.com/rosscyking1115/redteam-foundry/blob/main/",
        "https://github.com/rosscyking1115/redteam-foundry/tree/main/",
        RAW_HOST + "rosscyking1115/redteam-foundry/main/",
    )
    checked = 0
    for target in _targets():
        for prefix in prefixes:
            if target.startswith(prefix):
                rel = target[len(prefix) :].partition("#")[0]
                assert (PROJECT_ROOT / rel).exists(), (
                    f"README links {target!r}, but {rel!r} does not exist in this repository."
                )
                checked += 1
    assert checked >= 20, f"only {checked} in-repository links checked — the prefixes look stale"
