"""Command-line interface for the red-team harness.

Phases ship sub-commands as they land. Today: `version`, plus `corpora`
download and list (Phase 1). Stubs for Phases 2-7 are still here so
`redteam --help` doubles as a build roadmap.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Literal, cast

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

from redteam import __version__
from redteam.corpora import LOADERS
from redteam.schemas import AttackCase

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


@corpora_app.command("audit")
def corpora_audit(
    cache_root: Annotated[
        Path,
        typer.Option("--cache-root", help="Where corpora were cached."),
    ] = Path("data/cache"),
    only: Annotated[
        list[str] | None,
        typer.Option("--only", help="Restrict to specific sources (repeatable). Default: all."),
    ] = None,
    output_dir: Annotated[
        Path,
        typer.Option("--output", "-o", help="Directory for the audit artifacts."),
    ] = Path("reports/corpus_audit"),
    near_dup_threshold: Annotated[
        float,
        typer.Option("--near-dup-threshold", help="Jaccard similarity for near duplicates."),
    ] = 0.85,
) -> None:
    """Audit corpora for duplicates, overlap, and label issues.

    Loads the post-filter kept cases across the selected sources (combined,
    so cross-source duplicates surface), then writes a quality report, a data
    card, and the raw JSON to the output directory.
    """
    from redteam.corpora.datacard import render_datacard, render_quality_report
    from redteam.corpora.quality import audit_corpus

    sources = sorted(only) if only else sorted(LOADERS.keys())
    unknown = set(sources) - set(LOADERS.keys())
    if unknown:
        typer.echo(typer.style(f"Unknown source(s): {sorted(unknown)}", fg=typer.colors.RED))
        raise typer.Exit(code=2)

    all_cases: list[AttackCase] = []
    sources_meta: dict[str, str] = {}
    for source in sources:
        loader = LOADERS[source](cache_root=cache_root)
        typer.echo(f"-> {source}: loading ...")
        try:
            loader.download()
            kept, _ = loader.load()
        except Exception as exc:
            typer.echo(typer.style(f"   FAILED: {exc}", fg=typer.colors.RED))
            raise typer.Exit(code=1) from exc
        all_cases.extend(kept)
        sources_meta[source] = f"pinned {loader.pinned_revision[:12]}"

    if not all_cases:
        typer.echo(typer.style("No cases loaded - nothing to audit.", fg=typer.colors.RED))
        raise typer.Exit(code=1)

    report = audit_corpus(all_cases, near_dup_threshold=near_dup_threshold)
    title = sources[0] if len(sources) == 1 else f"combined ({len(sources)} sources)"

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "corpus_quality.json").write_text(
        report.model_dump_json(indent=2), encoding="utf-8"
    )
    (output_dir / "corpus_quality_report.md").write_text(
        render_quality_report(report, title=title), encoding="utf-8"
    )
    (output_dir / "corpus_datacard.md").write_text(
        render_datacard(report, title=title, sources_meta=sources_meta), encoding="utf-8"
    )

    typer.echo(
        typer.style(
            f"Audited {report.n_cases} cases: "
            f"{report.n_exact_duplicate_cases} exact-dup ({report.duplicate_rate:.1%}), "
            f"{report.n_cross_source_duplicate_groups} cross-source dup group(s), "
            f"{report.n_near_duplicate_pairs} near-dup pair(s), "
            f"{report.n_label_issues} label issue(s).",
            fg=typer.colors.GREEN,
        )
    )
    typer.echo(typer.style(f"Wrote: {output_dir}/", fg=typer.colors.BRIGHT_BLACK))


@corpora_app.command("audit-hf")
def corpora_audit_hf(
    dataset: Annotated[
        str,
        typer.Option("--dataset", help="Hugging Face dataset id, e.g. 'walledai/AdvBench'."),
    ],
    prompt_column: Annotated[
        str,
        typer.Option("--prompt-column", help="Column holding the prompt text."),
    ],
    split: Annotated[str, typer.Option("--split", help="Dataset split.")] = "train",
    config: Annotated[
        str | None, typer.Option("--config", help="HF dataset config/subset name.")
    ] = None,
    revision: Annotated[
        str | None, typer.Option("--revision", help="Pin a dataset commit/tag (recommended).")
    ] = None,
    limit: Annotated[int | None, typer.Option("--limit", help="Cap rows loaded.")] = None,
    output_dir: Annotated[
        Path,
        typer.Option("--output", "-o", help="Directory for the audit artifacts."),
    ] = Path("reports/hf_audit"),
    near_dup_threshold: Annotated[
        float,
        typer.Option("--near-dup-threshold", help="Jaccard similarity for near duplicates."),
    ] = 0.85,
) -> None:
    """Audit ANY Hugging Face adversarial dataset, not just the built-in four.

    Loads the dataset, runs the safety exclusion filter (so nothing excluded is
    audited or previewed), then writes the same quality report + data card.
    """
    from redteam.corpora._filters import filter_cases
    from redteam.corpora.datacard import render_datacard, render_quality_report
    from redteam.corpora.huggingface import load_hf_dataset
    from redteam.corpora.quality import audit_corpus

    typer.echo(f"-> loading {dataset} (split={split}) ...")
    try:
        raw = load_hf_dataset(
            dataset,
            prompt_column=prompt_column,
            split=split,
            config=config,
            revision=revision,
            limit=limit,
        )
    except Exception as exc:
        typer.echo(typer.style(f"   FAILED: {exc}", fg=typer.colors.RED))
        raise typer.Exit(code=1) from exc

    if not raw:
        typer.echo(typer.style("No rows loaded — check --prompt-column.", fg=typer.colors.RED))
        raise typer.Exit(code=1)

    kept, excluded = filter_cases(raw)
    if excluded:
        typer.echo(
            typer.style(
                f"   safety filter excluded {len(excluded)} of {len(raw)} row(s).",
                fg=typer.colors.YELLOW,
            )
        )
    if not kept:
        typer.echo(
            typer.style(
                "All rows excluded by the safety filter — nothing to audit.", fg=typer.colors.RED
            )
        )
        raise typer.Exit(code=1)

    report = audit_corpus(kept, near_dup_threshold=near_dup_threshold)
    provenance = f"hf:{dataset}" + (f"@{revision}" if revision else "") + f" (split={split})"

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "corpus_quality.json").write_text(
        report.model_dump_json(indent=2), encoding="utf-8"
    )
    (output_dir / "corpus_quality_report.md").write_text(
        render_quality_report(report, title=dataset), encoding="utf-8"
    )
    (output_dir / "corpus_datacard.md").write_text(
        render_datacard(report, title=dataset, sources_meta={"external": provenance}),
        encoding="utf-8",
    )

    typer.echo(
        typer.style(
            f"Audited {report.n_cases} kept case(s): "
            f"{report.n_exact_duplicate_cases} exact-dup ({report.duplicate_rate:.1%}), "
            f"{report.n_near_duplicate_pairs} near-dup pair(s), "
            f"languages={sorted(report.language_coverage)}, "
            f"{report.n_label_issues} label issue(s).",
            fg=typer.colors.GREEN,
        )
    )
    typer.echo(typer.style(f"Wrote: {output_dir}/", fg=typer.colors.BRIGHT_BLACK))


@corpora_app.command("staleness")
def corpora_staleness(
    cache_root: Annotated[
        Path,
        typer.Option("--cache-root", help="Where corpora were cached."),
    ] = Path("data/cache"),
    only: Annotated[
        list[str] | None,
        typer.Option("--only", help="Sources to score (repeatable). Default: all, combined."),
    ] = None,
    run: Annotated[
        list[Path] | None,
        typer.Option("--run", help="RunResult JSON(s) that used this corpus (repeatable)."),
    ] = None,
    output_dir: Annotated[
        Path,
        typer.Option("--output", "-o", help="Directory for the staleness artifacts."),
    ] = Path("reports/staleness"),
    near_dup_threshold: Annotated[
        float,
        typer.Option("--near-dup-threshold", help="Jaccard similarity for near duplicates."),
    ] = 0.85,
) -> None:
    """Score whether a benchmark still measures real risk (heuristic).

    Composes corpus signals (obsolete jailbreak-meme patterns, duplication)
    with run signals (universal-low-ASR, defence-insensitivity, judge
    disagreement) into a single heuristic staleness score. Pass `--run` for
    each evaluation JSON that used this corpus to enable the run components.
    """
    from redteam.orchestrator import RunResult
    from redteam.staleness import render_staleness_report, score_staleness

    sources = sorted(only) if only else sorted(LOADERS.keys())
    unknown = set(sources) - set(LOADERS.keys())
    if unknown:
        typer.echo(typer.style(f"Unknown source(s): {sorted(unknown)}", fg=typer.colors.RED))
        raise typer.Exit(code=2)

    all_cases: list[AttackCase] = []
    for source in sources:
        loader = LOADERS[source](cache_root=cache_root)
        try:
            loader.download()
            kept, _ = loader.load()
        except Exception as exc:
            typer.echo(typer.style(f"   {source} FAILED: {exc}", fg=typer.colors.RED))
            raise typer.Exit(code=1) from exc
        all_cases.extend(kept)

    runs: list[RunResult] = []
    for run_path in run or []:
        if not run_path.exists():
            typer.echo(typer.style(f"Run not found: {run_path}", fg=typer.colors.RED))
            raise typer.Exit(code=2)
        runs.append(RunResult.model_validate_json(run_path.read_text(encoding="utf-8")))

    title = sources[0] if len(sources) == 1 else f"combined ({len(sources)} sources)"
    report = score_staleness(all_cases, runs, title=title, near_dup_threshold=near_dup_threshold)

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "staleness.json").write_text(report.model_dump_json(indent=2), encoding="utf-8")
    (output_dir / "staleness_report.md").write_text(
        render_staleness_report(report), encoding="utf-8"
    )

    score_str = f"{report.staleness_score:.2f}" if report.staleness_score is not None else "n/a"
    typer.echo(
        typer.style(
            f"Staleness {score_str}/1.00 ({report.n_components_available}/"
            f"{len(report.components)} components, confidence: {report.confidence}). "
            f"{report.interpretation}",
            fg=typer.colors.GREEN,
        )
    )
    typer.echo(typer.style(f"Wrote: {output_dir}/", fg=typer.colors.BRIGHT_BLACK))


# ---------------------------------------------------------------------------
# `redteam benign ...` + `redteam compare-defences` (Phase 3)
# ---------------------------------------------------------------------------

benign_app = typer.Typer(
    name="benign",
    help="Benign control set for false-refusal-rate measurement (Phase 3).",
    no_args_is_help=True,
    add_completion=False,
)
app.add_typer(benign_app)


@benign_app.command("export")
def benign_export(
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="JSONL path (default depends on --multilingual)."),
    ] = None,
    multilingual: Annotated[
        bool,
        typer.Option("--multilingual", help="Export the multilingual benign set instead."),
    ] = False,
) -> None:
    """Write a benign control set to JSONL (for FRR runs / inspection)."""
    if multilingual:
        from redteam.multilingual import MULTILINGUAL_BENIGN, export_multilingual_jsonl

        path = export_multilingual_jsonl(output or Path("data/benign_multilingual.jsonl"))
        count = len(MULTILINGUAL_BENIGN)
    else:
        from redteam.benign import BENIGN_CONTROL, export_benign_jsonl

        path = export_benign_jsonl(output or Path("data/benign_control.jsonl"))
        count = len(BENIGN_CONTROL)

    typer.echo(typer.style(f"Wrote {count} benign cases to {path}", fg=typer.colors.GREEN))
    typer.echo(
        typer.style(
            "Run it per defence config (configs/run_benign_*.yaml), then feed the results to "
            "`redteam compare-defences --benign-run ...` or `redteam frr-by-language --run ...`.",
            fg=typer.colors.BRIGHT_BLACK,
        )
    )


@app.command(name="frr-by-language")
def frr_by_language_cmd(
    run: Annotated[
        Path,
        typer.Option("--run", "-r", help="RunResult JSON over a benign (multilingual) set."),
    ],
    output_dir: Annotated[
        Path,
        typer.Option("--output", "-o", help="Directory for the per-language FRR artifacts."),
    ] = Path("reports/frr_by_language"),
) -> None:
    """Break a benign run's false-refusal rate down by language.

    Uses each case's recorded `lang` (exact — distinguishes zh-Hant from
    zh-Hans) where known, else script-based detection of the prompt.
    """
    from redteam.benign import BENIGN_CONTROL
    from redteam.compare import frr_by_language, render_frr_by_language
    from redteam.multilingual import MULTILINGUAL_BENIGN
    from redteam.orchestrator import RunResult

    if not run.exists():
        typer.echo(typer.style(f"Run not found: {run}", fg=typer.colors.RED))
        raise typer.Exit(code=2)

    result = RunResult.model_validate_json(run.read_text(encoding="utf-8"))
    report = frr_by_language(result, [*BENIGN_CONTROL, *MULTILINGUAL_BENIGN])

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "frr_by_language.json").write_text(
        report.model_dump_json(indent=2), encoding="utf-8"
    )
    (output_dir / "frr_by_language.md").write_text(render_frr_by_language(report), encoding="utf-8")

    typer.echo(
        typer.style(
            f"Overall FRR {report.overall_frr:.1%} over {report.n_cases} case(s), "
            f"{len(report.rows)} language(s).",
            fg=typer.colors.GREEN,
        )
    )
    typer.echo(typer.style(f"Wrote: {output_dir}/", fg=typer.colors.BRIGHT_BLACK))


@app.command(name="compare-defences")
def compare_defences_cmd(
    run: Annotated[
        list[Path],
        typer.Option("--run", help="Adversarial RunResult JSON(s) (repeatable)."),
    ],
    benign_run: Annotated[
        list[Path] | None,
        typer.Option("--benign-run", help="RunResult JSON(s) over the benign control set."),
    ] = None,
    output_dir: Annotated[
        Path,
        typer.Option("--output", "-o", help="Directory for the comparison artifacts."),
    ] = Path("reports/defence_comparison"),
) -> None:
    """Compare defence configs on ASR, false-refusal rate, and safe usefulness.

    Adversarial and benign runs are matched by (target, defences). Pass
    `--benign-run` results (over the benign control set) to populate FRR and
    the combined safe-usefulness score.
    """
    from redteam.compare import compare_defences, render_defence_comparison
    from redteam.orchestrator import RunResult

    def _load(paths: list[Path]) -> list[RunResult]:
        loaded: list[RunResult] = []
        for p in paths:
            if not p.exists():
                typer.echo(typer.style(f"Run not found: {p}", fg=typer.colors.RED))
                raise typer.Exit(code=2)
            loaded.append(RunResult.model_validate_json(p.read_text(encoding="utf-8")))
        return loaded

    adversarial = _load(list(run))
    benign = _load(list(benign_run or []))

    report = compare_defences(adversarial, benign)

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "defence_comparison.json").write_text(
        report.model_dump_json(indent=2), encoding="utf-8"
    )
    (output_dir / "defence_comparison.md").write_text(
        render_defence_comparison(report), encoding="utf-8"
    )

    typer.echo(
        typer.style(
            f"Compared {report.n_adversarial_runs} config(s); "
            f"{report.n_configs_with_frr} with FRR / safe-usefulness.",
            fg=typer.colors.GREEN,
        )
    )
    typer.echo(typer.style(f"Wrote: {output_dir}/", fg=typer.colors.BRIGHT_BLACK))


# ---------------------------------------------------------------------------
# `redteam export-pack` (Phase 5)
# ---------------------------------------------------------------------------


@app.command(name="export-pack")
def export_pack_cmd(
    pack_id: Annotated[
        str,
        typer.Option("--pack-id", help="Identifier for the pack (also the output dir name)."),
    ],
    only: Annotated[
        list[str] | None,
        typer.Option("--only", help="Sources to include (repeatable). Default: all adversarial."),
    ] = None,
    version: Annotated[str, typer.Option("--version", help="Pack version.")] = "1.0.0",
    description: Annotated[str, typer.Option("--description", help="One-line description.")] = "",
    output_dir: Annotated[
        Path,
        typer.Option(
            "--output", "-o", help="Parent dir; the pack is written to <output>/<pack-id>."
        ),
    ] = Path("challenge_packs"),
    cache_root: Annotated[
        Path, typer.Option("--cache-root", help="Where corpora were cached.")
    ] = Path("data/cache"),
    limit: Annotated[int | None, typer.Option("--limit", help="Cap cases per source.")] = None,
    include_adversarial_prompts: Annotated[
        bool,
        typer.Option(
            "--include-adversarial-prompts",
            help="Ship raw adversarial prompts (default: redact to SHA-256 + preview).",
        ),
    ] = False,
) -> None:
    """Export a validated set of scenarios as a versioned challenge pack.

    Benign scenarios ship in full; adversarial scenarios are redacted by
    default. Writes pack.yaml + scenarios.jsonl + datacard.md.
    """
    from redteam.packs import build_challenge_pack, write_challenge_pack

    allowed = set(LOADERS) | {"benign_control", "benign_multilingual"}
    sources = sorted(only) if only else sorted(LOADERS.keys())
    unknown = set(sources) - allowed
    if unknown:
        typer.echo(typer.style(f"Unknown source(s): {sorted(unknown)}", fg=typer.colors.RED))
        raise typer.Exit(code=2)

    cases: list[AttackCase] = []
    for source in sources:
        if source == "benign_control":
            from redteam.benign import BENIGN_CONTROL

            picked = BENIGN_CONTROL
        elif source == "benign_multilingual":
            from redteam.multilingual import MULTILINGUAL_BENIGN

            picked = MULTILINGUAL_BENIGN
        else:
            loader = LOADERS[source](cache_root=cache_root)
            try:
                loader.download()
                picked, _ = loader.load()
            except Exception as exc:
                typer.echo(typer.style(f"   {source} FAILED: {exc}", fg=typer.colors.RED))
                raise typer.Exit(code=1) from exc
        cases.extend(picked[:limit] if limit is not None else picked)

    if not cases:
        typer.echo(typer.style("No cases to pack.", fg=typer.colors.RED))
        raise typer.Exit(code=1)

    pack, scenarios = build_challenge_pack(
        cases,
        pack_id=pack_id,
        version=version,
        description=description,
        include_adversarial_prompts=include_adversarial_prompts,
    )
    out = write_challenge_pack(pack, scenarios, output_dir / pack_id)

    typer.echo(
        typer.style(
            f"Packed {pack.n_scenarios} scenario(s) "
            f"({'redacted' if pack.scenarios_redacted else 'full prompts'}); "
            f"sources={pack.sources}, languages={pack.languages}.",
            fg=typer.colors.GREEN,
        )
    )
    typer.echo(typer.style(f"Wrote: {out}/", fg=typer.colors.BRIGHT_BLACK))


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
    asr_ci = (
        f" [95% CI {result.asr_ci_lo:.2%}, {result.asr_ci_hi:.2%}]"
        if result.asr_ci_lo is not None
        else ""
    )
    ref_ci = (
        f" [95% CI {result.refusal_rate_ci_lo:.2%}, {result.refusal_rate_ci_hi:.2%}]"
        if result.refusal_rate_ci_lo is not None
        else ""
    )
    typer.echo(
        typer.style(
            f"Done. {result.cases_total} cases, refusal_rate={result.refusal_rate:.2%}{ref_ci}, "
            f"ASR={result.asr:.2%}{asr_ci}, total ${result.total_cost_usd}",
            fg=typer.colors.GREEN,
        )
    )
    typer.echo(typer.style(f"Wrote: {written}", fg=typer.colors.BRIGHT_BLACK))


# ---------------------------------------------------------------------------
# `redteam score --run <path>` (Phase 4)
# ---------------------------------------------------------------------------


@app.command(name="score")
def score_cmd(
    run: Annotated[
        Path,
        typer.Option("--run", "-r", help="Path to a RunResult JSON written by `redteam run`."),
    ],
    cache_root: Annotated[
        Path,
        typer.Option(
            "--cache-root", help="Where the response cache lives. Judge calls hit this same store."
        ),
    ] = Path("data/cache/responses"),
    budget_usd: Annotated[
        float,
        typer.Option("--budget-usd", help="Per-run cap on judge spend in USD."),
    ] = 2.00,
    output: Annotated[
        Path | None,
        typer.Option(
            "--output", "-o", help="Where to write the judged JSON. Default: <run>.judged.json"
        ),
    ] = None,
) -> None:
    """Run the LLM-judge over an existing RunResult JSON and write a judged copy."""
    import asyncio
    from decimal import Decimal as _D

    from redteam.budget import BudgetExceeded
    from redteam.orchestrator import score_run

    if not run.exists():
        typer.echo(typer.style(f"Run not found: {run}", fg=typer.colors.RED))
        raise typer.Exit(code=2)

    typer.echo(typer.style(f"Scoring: {run.name}  budget=${budget_usd}", fg=typer.colors.CYAN))
    try:
        scored = asyncio.run(
            score_run(
                run, cache_root=cache_root, budget_usd=_D(str(budget_usd)), output_path=output
            )
        )
    except BudgetExceeded as exc:
        typer.echo(typer.style(f"BudgetExceeded: {exc}", fg=typer.colors.RED))
        raise typer.Exit(code=1) from exc

    out_path = output or run.with_name(run.stem + ".judged.json")
    judge_asr_ci_str = (
        f" [95% CI {scored.judge_asr_rate_ci_lo:.2%}, {scored.judge_asr_rate_ci_hi:.2%}]"
        if scored.judge_asr_rate_ci_lo is not None
        else ""
    )
    judge_ref_ci_str = (
        f" [95% CI {scored.judge_refusal_rate_ci_lo:.2%}, {scored.judge_refusal_rate_ci_hi:.2%}]"
        if scored.judge_refusal_rate_ci_lo is not None
        else ""
    )
    typer.echo(
        typer.style(
            f"Done. judged={scored.judge_n_judged}  failed={scored.judge_n_failed}  "
            f"judge_asr={scored.judge_asr_rate:.2%}{judge_asr_ci_str}  "
            f"judge_refusal={scored.judge_refusal_rate:.2%}{judge_ref_ci_str}  "
            f"judge cost ${scored.judge_total_cost_usd}",
            fg=typer.colors.GREEN,
        )
    )
    typer.echo(typer.style(f"Wrote: {out_path}", fg=typer.colors.BRIGHT_BLACK))


@app.command(name="export-human-review")
def export_human_review_cmd(
    run: Annotated[
        Path,
        typer.Option("--run", "-r", help="Path to a (preferably judged) RunResult JSON."),
    ],
    sample_pct: Annotated[
        float,
        typer.Option("--sample-pct", help="Fraction of cases to sample (0..1). Default 0.05."),
    ] = 0.05,
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="CSV path. Default: <run>.human-review.csv"),
    ] = None,
) -> None:
    """Export a deterministic ~N% sample of cases as a CSV for human labelling."""
    from redteam.scorers import export_for_human_review

    if not run.exists():
        typer.echo(typer.style(f"Run not found: {run}", fg=typer.colors.RED))
        raise typer.Exit(code=2)
    out = export_for_human_review(run, sample_pct=sample_pct, output_csv=output)
    typer.echo(typer.style(f"Wrote: {out}", fg=typer.colors.GREEN))
    typer.echo(
        typer.style(
            "Fill in the human_asr / human_refusal columns (0/1), save, then run "
            "`redteam kappa --csv <path>` to compute Cohen's kappa.",
            fg=typer.colors.BRIGHT_BLACK,
        )
    )


@app.command(name="kappa")
def kappa_cmd(
    csv: Annotated[
        Path,
        typer.Option("--csv", help="Path to the human-filled review CSV."),
    ],
) -> None:
    """Compute Cohen's kappa between judge and human labels on a filled CSV."""
    from redteam.scorers import compute_kappa

    if not csv.exists():
        typer.echo(typer.style(f"CSV not found: {csv}", fg=typer.colors.RED))
        raise typer.Exit(code=2)

    report = compute_kappa(csv)
    typer.echo(
        typer.style(
            f"n_rows={report.n_rows}  n_human_filled={report.n_human_filled}",
            fg=typer.colors.CYAN,
        )
    )
    typer.echo(
        f"  asr      kappa={report.asr.kappa:+.3f}  alpha={report.asr.alpha:+.3f}  "
        f"agreement={report.asr.agreement:.2%}  n={report.asr.n}"
    )
    typer.echo(
        f"  refusal  kappa={report.refusal.kappa:+.3f}  alpha={report.refusal.alpha:+.3f}  "
        f"agreement={report.refusal.agreement:.2%}  n={report.refusal.n}"
    )
    if report.asr.kappa < 0.6 or report.asr.alpha < 0.667:
        typer.echo(
            typer.style(
                "WARN: ASR agreement below acceptance thresholds (kappa>=0.6, alpha>=0.667). "
                "Either expand the human sample or revisit the judge prompt.",
                fg=typer.colors.YELLOW,
            )
        )


# ---------------------------------------------------------------------------
# `redteam cross-judge --run <judged.json>` (ST2.1 closeout)
# ---------------------------------------------------------------------------


@app.command(name="cross-judge")
def cross_judge_cmd(
    run: Annotated[
        Path,
        typer.Option("--run", "-r", help="Path to a *.judged.json written by `redteam score`."),
    ],
    judge2_model: Annotated[
        str,
        typer.Option(
            "--judge2-model",
            help="Second judge model to compare against the primary (Haiku 4.5) judge.",
        ),
    ] = "claude-sonnet-4-6",
    cache_root: Annotated[
        Path,
        typer.Option("--cache-root", help="Where the response cache lives."),
    ] = Path("data/cache/responses"),
    budget_usd: Annotated[
        float,
        typer.Option("--budget-usd", help="Per-run cap on second-judge spend in USD."),
    ] = 2.00,
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Where to write. Default: <run>.cross-judged.json"),
    ] = None,
) -> None:
    """Run a second LLM judge over an already-judged run; report kappa + alpha.

    This is the primary judge-validation step in 2026 best practice (vs the
    older "5% human spot-check" — which is still valuable but slower). Per
    kit Lesson L4: judges have biases; cross-judge agreement is the cheap,
    fast, reproducible alternative.
    """
    import asyncio
    from decimal import Decimal as _D

    from redteam.budget import BudgetExceeded
    from redteam.orchestrator import cross_judge_run

    if not run.exists():
        typer.echo(typer.style(f"Run not found: {run}", fg=typer.colors.RED))
        raise typer.Exit(code=2)

    typer.echo(
        typer.style(
            f"Cross-judging: {run.name}  judge2={judge2_model}  budget=${budget_usd}",
            fg=typer.colors.CYAN,
        )
    )
    try:
        scored = asyncio.run(
            cross_judge_run(
                run,
                judge2_model=judge2_model,
                cache_root=cache_root,
                budget_usd=_D(str(budget_usd)),
                output_path=output,
            )
        )
    except (BudgetExceeded, ValueError) as exc:
        typer.echo(typer.style(f"{type(exc).__name__}: {exc}", fg=typer.colors.RED))
        raise typer.Exit(code=1) from exc

    out_path = output or run.with_name(run.stem + ".cross-judged.json")
    j2_asr_ci = (
        f" [95% CI {scored.judge2_asr_rate_ci_lo:.2%}, {scored.judge2_asr_rate_ci_hi:.2%}]"
        if scored.judge2_asr_rate_ci_lo is not None
        else ""
    )
    j2_ref_ci = (
        f" [95% CI {scored.judge2_refusal_rate_ci_lo:.2%}, {scored.judge2_refusal_rate_ci_hi:.2%}]"
        if scored.judge2_refusal_rate_ci_lo is not None
        else ""
    )
    typer.echo("")
    typer.echo(
        typer.style(
            f"Judge1 ({scored.judge_model_version}):",
            fg=typer.colors.BRIGHT_BLACK,
        )
    )
    typer.echo(
        f"  asr={scored.judge_asr_rate:.2%}  refusal={scored.judge_refusal_rate:.2%}  "
        f"n={scored.judge_n_judged}"
    )
    typer.echo(
        typer.style(
            f"Judge2 ({scored.judge2_model_version}):",
            fg=typer.colors.BRIGHT_BLACK,
        )
    )
    typer.echo(
        f"  asr={scored.judge2_asr_rate:.2%}{j2_asr_ci}  "
        f"refusal={scored.judge2_refusal_rate:.2%}{j2_ref_ci}  "
        f"n={scored.judge2_n_judged}  cost=${scored.judge2_total_cost_usd}"
    )
    typer.echo(
        typer.style(
            f"Cross-judge agreement (n={scored.cross_judge_agreement_n}):",
            fg=typer.colors.CYAN,
        )
    )
    typer.echo(
        f"  asr      kappa={scored.cross_judge_asr_kappa:+.3f}  alpha={scored.cross_judge_asr_alpha:+.3f}"
    )
    typer.echo(
        f"  refusal  kappa={scored.cross_judge_refusal_kappa:+.3f}  alpha={scored.cross_judge_refusal_alpha:+.3f}"
    )
    if (scored.cross_judge_asr_kappa or 0) < 0.6 or (scored.cross_judge_asr_alpha or 0) < 0.667:
        typer.echo(
            typer.style(
                "WARN: cross-judge ASR agreement below thresholds (kappa>=0.6, alpha>=0.667). "
                "Treat the headline number with caution.",
                fg=typer.colors.YELLOW,
            )
        )
    else:
        typer.echo(
            typer.style(
                "Cross-judge agreement passes thresholds — judge1 verdict is corroborated.",
                fg=typer.colors.GREEN,
            )
        )
    typer.echo(typer.style(f"Wrote: {out_path}", fg=typer.colors.BRIGHT_BLACK))


# ---------------------------------------------------------------------------
# `redteam export-inspect --run <result.json>` (ST2.6)
# ---------------------------------------------------------------------------


@app.command(name="export-inspect")
def export_inspect_cmd(
    run: Annotated[
        Path,
        typer.Option(
            "--run", "-r", help="RunResult JSON from `redteam run` / `score` / `cross-judge`."
        ),
    ],
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Output path. Default: <run>.inspect.eval"),
    ] = None,
    fmt: Annotated[
        str,
        typer.Option(
            "--format", "-f", help="Inspect log format: `eval`, `json`, or `auto` (by extension)."
        ),
    ] = "auto",
) -> None:
    """Export a RunResult to a UK AISI Inspect AI eval log (`.eval` / `.json`).

    The output opens directly in `inspect view` and loads with
    `inspect_ai.log.read_eval_log()`. `inspect_ai` is an optional dependency —
    install it with `uv pip install -e ".[inspect]"`.
    """
    from redteam.inspect_export import export_inspect_log
    from redteam.orchestrator import RunResult

    if not run.exists():
        typer.echo(typer.style(f"Run not found: {run}", fg=typer.colors.RED))
        raise typer.Exit(code=2)
    if fmt not in {"eval", "json", "auto"}:
        typer.echo(
            typer.style(f"Invalid --format: {fmt} (use eval, json, or auto)", fg=typer.colors.RED)
        )
        raise typer.Exit(code=2)

    ext = ".json" if fmt == "json" else ".eval"
    out_path = output or run.with_name(run.stem + ".inspect" + ext)
    try:
        result = RunResult.model_validate_json(run.read_text(encoding="utf-8"))
        export_inspect_log(result, out_path, fmt=cast(Literal["eval", "json", "auto"], fmt))
    except RuntimeError as exc:
        typer.echo(typer.style(str(exc), fg=typer.colors.RED))
        raise typer.Exit(code=1) from exc

    typer.echo(
        typer.style(
            f"Exported {result.cases_total} cases to an Inspect AI eval log.",
            fg=typer.colors.GREEN,
        )
    )
    typer.echo(typer.style(f"Wrote: {out_path}", fg=typer.colors.BRIGHT_BLACK))
    typer.echo(
        typer.style(
            f"View it with:  inspect view --log-dir {out_path.parent}",
            fg=typer.colors.BRIGHT_BLACK,
        )
    )


if __name__ == "__main__":
    app()
