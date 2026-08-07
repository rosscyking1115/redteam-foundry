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


# ---------------------------------------------------------------------------
# The gated-dataset hint (0.5.1)
# ---------------------------------------------------------------------------


def test_gated_hint_fires_on_the_real_hub_message() -> None:
    """The message the Hub actually returned, kept verbatim as the fixture.

    `walledai/AdvBench` was the example printed in `--help` until it became
    gated, so anyone copying it out of the help text hit this. The exact wording
    below is what the Hub produced.
    """
    from redteam.cli import _looks_gated

    real = Exception(
        "Dataset 'walledai/AdvBench' is a gated dataset on the Hub. Visit the "
        "dataset page at https://huggingface.co/datasets/walledai/AdvBench to "
        "ask for access."
    )
    assert _looks_gated(real) is True


def test_gated_hint_does_not_fire_on_an_ordinary_failure() -> None:
    """A hint on every error is a hint on none of them."""
    from redteam.cli import _looks_gated

    assert _looks_gated(Exception("Connection reset by peer")) is False
    assert _looks_gated(ValueError("prompt-column 'nope' not in dataset columns ['goal']")) is False


def test_the_help_example_names_an_ungated_dataset() -> None:
    """The example in `--help` is the one place a new user is guaranteed to look.

    Pinned by name: the previous example silently became gated, and nothing in
    the repository could tell. This does not prove the dataset is *still*
    ungated — only a live call can — but it does stop the known-gated one
    returning by accident.
    """
    result = CliRunner().invoke(app, ["corpora", "audit-hf", "--help"])
    assert result.exit_code == 0
    assert "walledai/AdvBench" not in result.stdout, (
        "the help example names a dataset that is gated on the Hub"
    )
    assert "JailbreakBench/JBB-Behaviors" in result.stdout
