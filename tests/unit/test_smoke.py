"""Phase 0 smoke test — confirms the package imports and the CLI is wired.

Defends: the package imports and the CLI is wired — the install/version claim.
"""

from __future__ import annotations

from typer.testing import CliRunner

from redteam import __version__
from redteam.cli import app


def test_package_version_is_set() -> None:
    """That a version exists at all — deliberately not *which* one.

    This assertion used to read `__version__ == "0.3.0"`, a third hardcoded copy
    of a number already written in `pyproject.toml` and in `__init__.py`. It was
    green throughout the 0.4.0 release, because the code and the test carried the
    *same wrong value* and agreed with each other while the package metadata said
    something else. A test named for a property it does not check is worse than
    no test: it occupies the place where the real check would go.

    Whether the version is *correct* is `tests/unit/test_version.py`, which
    compares it against `pyproject.toml` and the installed distribution.
    """
    assert __version__ and __version__ != "0.0.0+unknown"


def test_cli_version_command_runs() -> None:
    """Exit code and wiring only.

    `__version__ in result.stdout` compares the code to itself and would pass on
    any value, correct or not. It is kept here as a smoke check that the command
    is wired at all; `test_version.py` compares the printed string to the
    installed distribution, which is the claim a user cares about.
    """
    runner = CliRunner()
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout
