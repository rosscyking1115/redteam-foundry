"""Command-line interface for the red-team harness.

Phase 0 ships `version` plus stubs for every planned sub-command, so the
`redteam --help` output doubles as a build roadmap.

- `redteam corpora ...`  -> Phase 1
- `redteam targets ...`  -> Phase 2
- `redteam run ...`      -> Phase 3
- `redteam score ...`    -> Phase 4
- `redteam report ...`   -> Phase 6
- `redteam smoke ...`    -> Phase 7 (CI entry-point)
"""

from __future__ import annotations

import typer

from redteam import __version__

app = typer.Typer(
    name="redteam",
    help="LLM red-team evaluation harness - see METHODOLOGY.md.",
    no_args_is_help=True,
    add_completion=False,
)


def _not_yet(phase: int, command: str) -> None:
    msg = (
        f"`redteam {command}` is not implemented yet (lands in Phase {phase}). "
        "See PROJECT-1-KIT.md section 7 for the build plan."
    )
    typer.echo(typer.style(msg, fg=typer.colors.YELLOW))
    raise typer.Exit(code=0)


@app.command(name="version")
def version_cmd() -> None:
    """Print the installed harness version."""
    typer.echo(__version__)


@app.command(name="corpora")
def corpora_cmd() -> None:
    """[Phase 1] Download, filter, and list adversarial corpora."""
    _not_yet(1, "corpora")


@app.command(name="targets")
def targets_cmd() -> None:
    """[Phase 2] List configured target adapters and run a smoke ping."""
    _not_yet(2, "targets")


@app.command(name="run")
def run_cmd() -> None:
    """[Phase 3] Run an evaluation from a YAML config (with budget cap)."""
    _not_yet(3, "run")


@app.command(name="score")
def score_cmd() -> None:
    """[Phase 4] Re-score a cached run without re-querying targets."""
    _not_yet(4, "score")


@app.command(name="report")
def report_cmd() -> None:
    """[Phase 6] Build a Markdown / HTML report from a scored run."""
    _not_yet(6, "report")


@app.command(name="smoke")
def smoke_cmd() -> None:
    """[Phase 7] Stubbed end-to-end smoke run for CI (no real API calls)."""
    _not_yet(7, "smoke")


if __name__ == "__main__":
    app()
