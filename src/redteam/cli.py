"""Command-line interface for the red-team harness.

Phases ship sub-commands as they land. Today: `version`, plus `corpora`
download and list (Phase 1). Stubs for Phases 2-7 are still here so
`redteam --help` doubles as a build roadmap.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

from redteam import __version__
from redteam.corpora import LOADERS

# Load .env from the current working directory if present. Best-effort:
# never fails the CLI if .env is missing. Real auth errors surface later
# as ConfigError from the relevant adapter at __init__ time.
load_dotenv()

app = typer.Typer(
    name="redteam",
    help="LLM red-team evaluation harness - see METHODOLOGY.md.",
    no_args_is_help=True,
    add_completion=False,
)

corpora_app = typer.Typer(
    name="corpora",
    help="Download, filter, and inspect adversarial corpora (Phase 1).",
    no_args_is_help=True,
    add_completion=False,
)
app.add_typer(corpora_app)

_console = Console()


def _not_yet(phase: int, command: str) -> None:
    msg = (
        f"`redteam {command}` is not implemented yet (lands in Phase {phase}). "
        "See PROJECT-1-KIT.md section 7 for the build plan."
    )
    typer.echo(typer.style(msg, fg=typer.colors.YELLOW))
    raise typer.Exit(code=0)


# ---------------------------------------------------------------------------
# Top-level commands
# ---------------------------------------------------------------------------


@app.command(name="version")
def version_cmd() -> None:
    """Print the installed harness version."""
    typer.echo(__version__)


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


# ---------------------------------------------------------------------------
# `redteam corpora ...`
# ---------------------------------------------------------------------------


@corpora_app.command("download")
def corpora_download(
    cache_root: Annotated[
        Path,
        typer.Option("--cache-root", help="Where to materialise raw corpus files."),
    ] = Path("data/cache"),
    only: Annotated[
        list[str] | None,
        typer.Option(
            "--only", help="Restrict to specific sources (repeatable). Default: all four."
        ),
    ] = None,
) -> None:
    """Download and cache the configured adversarial corpora.

    Idempotent — re-running skips sources that are already cached.
    Network-bound: pulls AdvBench, JailbreakBench (HF), HarmBench from
    pinned commits. AgentDojo Phase-1 cases are embedded.
    """
    sources = sorted(only) if only else sorted(LOADERS.keys())  # only=None means all
    unknown = set(sources) - set(LOADERS.keys())
    if unknown:
        typer.echo(typer.style(f"Unknown source(s): {sorted(unknown)}", fg=typer.colors.RED))
        raise typer.Exit(code=2)

    for source in sources:
        loader = LOADERS[source](cache_root=cache_root)
        typer.echo(f"-> {source}: downloading ...")
        try:
            loader.download()
        except Exception as exc:
            typer.echo(typer.style(f"   FAILED: {exc}", fg=typer.colors.RED))
            raise typer.Exit(code=1) from exc
        typer.echo(typer.style("   ok", fg=typer.colors.GREEN))


@corpora_app.command("list")
def corpora_list(
    cache_root: Annotated[
        Path,
        typer.Option("--cache-root", help="Where corpora were cached."),
    ] = Path("data/cache"),
) -> None:
    """Load each cached corpus, apply the exclusion filter, print a summary.

    Triggers `download()` first (idempotent, no-op when cached) so this
    command always works on a fresh clone after a single CLI call.
    """
    table = Table(title="Adversarial corpora — post-filter summary", show_lines=False)
    table.add_column("Source", style="cyan", no_wrap=True)
    table.add_column("Raw", justify="right")
    table.add_column("Kept", justify="right", style="green")
    table.add_column("Excluded", justify="right", style="red")
    table.add_column("Excluded by topic", style="dim")
    table.add_column("Pinned revision", no_wrap=True, style="dim")

    totals = {"raw": 0, "kept": 0, "excluded": 0}

    for source in sorted(LOADERS.keys()):
        loader = LOADERS[source](cache_root=cache_root)
        try:
            loader.download()
            _, stats = loader.load()
        except Exception as exc:
            table.add_row(
                source,
                "-",
                "-",
                "-",
                f"[red]error: {exc}[/red]",
                loader.pinned_revision[:12],
            )
            continue

        totals["raw"] += stats.raw_count
        totals["kept"] += stats.kept_count
        totals["excluded"] += stats.excluded_count
        excluded_bd = (
            ", ".join(f"{k}={v}" for k, v in sorted(stats.excluded_by_topic.items())) or "-"
        )
        table.add_row(
            stats.source,
            str(stats.raw_count),
            str(stats.kept_count),
            str(stats.excluded_count),
            excluded_bd,
            stats.pinned_revision[:12],
        )

    table.add_section()
    table.add_row(
        "TOTAL",
        str(totals["raw"]),
        str(totals["kept"]),
        str(totals["excluded"]),
        "",
        "",
    )
    _console.print(table)
    if totals["kept"] < 200:
        typer.echo(
            typer.style(
                f"\nWARN: {totals['kept']} kept cases is below the Phase-1 acceptance "
                "criterion of >=200. Did all loaders run?",
                fg=typer.colors.YELLOW,
            )
        )


# ---------------------------------------------------------------------------
# `redteam targets ...` (Phase 2)
# ---------------------------------------------------------------------------

targets_app = typer.Typer(
    name="targets",
    help="List configured target adapters and run a smoke ping (Phase 2).",
    no_args_is_help=True,
    add_completion=False,
)
app.add_typer(targets_app)


@targets_app.command("list")
def targets_list() -> None:
    """List configured target adapters and their pinned model versions."""
    from redteam.targets import TARGETS

    table = Table(title="Configured target adapters", show_lines=False)
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Class", style="dim")
    table.add_column("Model version", no_wrap=True)
    table.add_column("Provider")
    for tid, cls in sorted(TARGETS.items()):
        provider = (
            "anthropic"
            if "Anthropic" in cls.__name__
            else "ollama"
            if "Ollama" in cls.__name__
            else "openai"
            if "OpenAI" in cls.__name__
            else "?"
        )
        table.add_row(tid, cls.__name__, cls.model_version, provider)
    _console.print(table)


@targets_app.command("ping")
def targets_ping(
    target: Annotated[
        str,
        typer.Option("--target", "-t", help="Target id from `redteam targets list`."),
    ] = "claude-sonnet-4-6",
    prompt: Annotated[
        str,
        typer.Option("--prompt", "-p", help="Prompt to send."),
    ] = "What is 2+2?",
    max_tokens: Annotated[
        int,
        typer.Option("--max-tokens", help="Cap on output tokens."),
    ] = 64,
) -> None:
    """Send a single prompt to a target and print the response.

    Goes through the budget guard. Use the smallest possible max_tokens
    while debugging. Does NOT use the response cache (so reruns hit the API).
    """
    import asyncio

    from redteam.budget import BudgetExceeded
    from redteam.schemas import Message
    from redteam.targets import TARGETS, ConfigError, OllamaUnavailable

    if target not in TARGETS:
        typer.echo(
            typer.style(
                f"Unknown target {target!r}. Try `redteam targets list`.", fg=typer.colors.RED
            )
        )
        raise typer.Exit(code=2)

    try:
        instance = TARGETS[target]()
    except (ConfigError, OllamaUnavailable) as exc:
        typer.echo(typer.style(f"{type(exc).__name__}: {exc}", fg=typer.colors.RED))
        raise typer.Exit(code=1) from exc

    async def go() -> None:
        try:
            resp = await instance.send(
                [Message(role="user", content=prompt)], max_tokens=max_tokens
            )
        except BudgetExceeded as exc:
            typer.echo(typer.style(f"BudgetExceeded: {exc}", fg=typer.colors.RED))
            raise typer.Exit(code=1) from exc
        typer.echo(typer.style(resp.response_text, fg=typer.colors.GREEN))
        typer.echo("")
        typer.echo(
            typer.style(
                f"[{resp.target_id} | {resp.input_tokens} in / {resp.output_tokens} out | "
                f"${resp.cost_usd} | {resp.latency_ms} ms]",
                fg=typer.colors.BRIGHT_BLACK,
            )
        )

    asyncio.run(go())


# ---------------------------------------------------------------------------
# `redteam run --config <path>` (Phase 3)
# ---------------------------------------------------------------------------


@app.command(name="run")
def run_cmd(
    config: Annotated[
        Path,
        typer.Option("--config", "-c", help="Path to a YAML run config under configs/."),
    ],
    cache_root: Annotated[
        Path,
        typer.Option("--cache-root", help="Where to put the response cache."),
    ] = Path("data/cache/responses"),
    output_dir: Annotated[
        Path | None,
        typer.Option("--output-dir", help="Override the output directory."),
    ] = None,
) -> None:
    """Run an evaluation from a YAML run config and write the JSON result."""
    import asyncio

    from redteam.budget import BudgetExceeded
    from redteam.orchestrator import RunConfig, run, write_result
    from redteam.targets import ConfigError, OllamaUnavailable

    if not config.exists():
        typer.echo(typer.style(f"Config not found: {config}", fg=typer.colors.RED))
        raise typer.Exit(code=2)

    cfg = RunConfig.from_yaml(config)
    typer.echo(
        typer.style(
            f"Run: {cfg.name}  target={cfg.target}  "
            f"defences={[d.id for d in cfg.defences]}  cap=${cfg.budget_usd}",
            fg=typer.colors.CYAN,
        )
    )

    try:
        result = asyncio.run(run(cfg, cache_root=cache_root))
    except (ConfigError, OllamaUnavailable, BudgetExceeded) as exc:
        typer.echo(typer.style(f"{type(exc).__name__}: {exc}", fg=typer.colors.RED))
        raise typer.Exit(code=1) from exc

    out = output_dir or cfg.output_dir
    written = write_result(result, out)
    typer.echo(
        typer.style(
            f"Done. {result.cases_total} cases, refusal_rate={result.refusal_rate:.2%}, "
            f"ASR={result.asr:.2%}, total ${result.total_cost_usd}",
            fg=typer.colors.GREEN,
        )
    )
    typer.echo(typer.style(f"Wrote: {written}", fg=typer.colors.BRIGHT_BLACK))
