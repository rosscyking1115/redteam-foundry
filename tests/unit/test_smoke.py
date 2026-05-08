"""Phase 0 smoke test — confirms the package imports and the CLI is wired."""

from __future__ import annotations

from typer.testing import CliRunner

from redteam import __version__
from redteam.cli import app


def test_package_version_is_set() -> None:
    assert __version__ == "0.1.0"


def test_cli_version_command_runs() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout
