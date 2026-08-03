"""`redteam version` must report the version that was actually installed.

This exists because it failed. `src/redteam/__init__.py` carried a hardcoded
`__version__` kept in step with `pyproject.toml` by hand, and the 0.4.0 release
bumped one and not the other. The published 0.4.0 wheel therefore contains
`METADATA: Version: 0.4.0` alongside code saying `0.3.0`, so anyone installing
0.4.0 and running `redteam version` is told 0.3.0.

Nothing caught it. The README audit's "run every command shown" step did, which
is the argument for that step: a version string is a claim, and a claim nobody
executes is a claim nobody checks.

`__version__` now reads the installed distribution metadata, so there is one
source of truth. These tests pin the property rather than the mechanism — they
fail on any future arrangement where the code and the package disagree.
"""

from __future__ import annotations

import tomllib
from importlib.metadata import version as installed_version
from pathlib import Path

import redteam

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _declared_version() -> str:
    config = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    declared = config["project"]["version"]
    assert isinstance(declared, str) and declared, "pyproject.toml declares no version"
    return declared


def test_package_version_matches_pyproject() -> None:
    """The drift that shipped in 0.4.0, pinned so it cannot recur silently."""
    assert redteam.__version__ == _declared_version(), (
        f"redteam.__version__ is {redteam.__version__!r} but pyproject.toml declares "
        f"{_declared_version()!r}. `redteam version` would report the wrong number to "
        "every user of the published package."
    )


def test_package_version_matches_the_installed_distribution() -> None:
    """Guards the other direction: an editable install left behind by a bump."""
    assert redteam.__version__ == installed_version("redteam-foundry")


def test_version_is_not_the_unknown_placeholder() -> None:
    """The source-tree fallback must never be what a test run measures.

    If it were, both tests above could pass or fail for reasons unrelated to the
    version at all — an unknown placeholder is exactly the kind of value that
    makes a check mean nothing.
    """
    assert redteam.__version__ != "0.0.0+unknown", (
        "the package is not installed, so these tests are not measuring a real version"
    )


def test_the_cli_reports_that_same_version() -> None:
    """`redteam version` is the surface a user actually sees."""
    from typer.testing import CliRunner

    from redteam.cli import app

    result = CliRunner().invoke(app, ["version"])
    assert result.exit_code == 0
    assert result.stdout.strip() == redteam.__version__
