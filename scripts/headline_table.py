"""Regenerate the headline results table (METHODOLOGY.md section 8) from the
cached run artifacts in ``results/``.

This is the one-command repro behind the README's headline finding. It does
**not** call any paid API: it reads the committed-locally cross-judged run
JSONs, recomputes judge attack-success rate (ASR) and a 95% percentile-bootstrap
confidence interval per evaluation cell straight from the per-case ``judge_asr``
labels, and prints the two Markdown tables that appear in METHODOLOGY.md section
8. With ``--check`` it also asserts every recomputed number matches the frozen
published value, so CI (or a reviewer) can prove the table still traces to the
artifacts.

The run artifacts themselves are gitignored (they contain prompt and response
text; see ETHICS.md), but they are free and deterministic to regenerate from the
response cache with ``redteam run`` / ``score`` / ``cross-judge`` — every API
call is cached by ``(target_id, model_version, hash(messages))``.

Run from the repo root:

    python scripts/headline_table.py            # print the tables
    python scripts/headline_table.py --check     # print + assert vs frozen numbers

Exit code is non-zero if a cell's artifact is missing or (under ``--check``) a
number has drifted from METHODOLOGY.md section 8.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

from redteam.stats import bootstrap_proportion_ci

REPO_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = REPO_ROOT / "results"


@dataclass(frozen=True)
class Cell:
    """One evaluation cell and its frozen published value (METHODOLOGY.md section 8)."""

    benchmark: str
    target: str
    defence: str
    glob: str  # prefix pattern under results/, before the run timestamp
    exp_asr_pct: int  # published judge ASR, percent
    exp_ci: tuple[int, int]  # published 95% bootstrap CI, percent
    exp_kappa: float  # published cross-judge ASR Cohen's kappa


# The 12 evaluation cells. Frozen values mirror METHODOLOGY.md section 8; the
# `glob` locates the cached cross-judged artifact regardless of run timestamp.
CELLS: list[Cell] = [
    # AdvBench — direct attacks, n = 100 per cell.
    Cell("AdvBench", "Sonnet 4.6", "baseline", "anthropic-baseline-*", 0, (0, 0), 1.0),
    Cell("AdvBench", "Sonnet 4.6", "full-stack", "anthropic-full-stack-*", 0, (0, 0), 1.0),
    Cell("AdvBench", "Llama 3.1 8B", "baseline", "local-llama31-baseline-*", 1, (0, 3), 1.0),
    Cell("AdvBench", "Llama 3.1 8B", "full-stack", "local-llama31-full-stack-*", 0, (0, 0), 1.0),
    # AgentDojo — static indirect injection, n = 50 per cell.
    Cell("AgentDojo", "Sonnet 4.6", "baseline", "agentdojo-baseline-*", 0, (0, 0), 1.0),
    Cell("AgentDojo", "Sonnet 4.6", "+ spotlighting", "agentdojo-spotlighting-*", 0, (0, 0), 1.0),
    Cell("AgentDojo", "Sonnet 4.6", "+ SecAlign", "agentdojo-secalign-*", 0, (0, 0), 1.0),
    Cell(
        "AgentDojo",
        "Sonnet 4.6",
        "full prompt stack",
        "agentdojo-full-prompt-stack-*",
        0,
        (0, 0),
        1.0,
    ),
    Cell("AgentDojo", "Llama 3.1 8B", "baseline", "agentdojo-local-baseline-*", 4, (0, 10), 1.0),
    Cell(
        "AgentDojo",
        "Llama 3.1 8B",
        "+ spotlighting",
        "agentdojo-local-spotlighting-*",
        0,
        (0, 0),
        1.0,
    ),
    Cell("AgentDojo", "Llama 3.1 8B", "+ SecAlign", "agentdojo-local-secalign-*", 0, (0, 0), 1.0),
    Cell(
        "AgentDojo",
        "Llama 3.1 8B",
        "full prompt stack",
        "agentdojo-local-full_prompt_stack-*",
        0,
        (0, 0),
        1.0,
    ),
]


@dataclass(frozen=True)
class Recomputed:
    """A cell's ASR / CI / kappa recomputed live from its cached artifact."""

    n: int
    asr_pct: int
    ci: tuple[int, int]
    kappa: float


def _find_artifact(cell: Cell) -> Path:
    """Locate the newest cached cross-judged artifact for a cell."""
    matches = sorted(RESULTS_DIR.glob(f"{cell.glob}judged.cross-judged.json"))
    if not matches:
        raise FileNotFoundError(
            f"no cross-judged artifact for {cell.benchmark}/{cell.target}/{cell.defence} "
            f"(pattern results/{cell.glob}judged.cross-judged.json). Regenerate it with "
            f"`redteam run` / `score` / `cross-judge` (free from the response cache)."
        )
    return matches[-1]


def recompute(cell: Cell) -> Recomputed:
    """Recompute judge ASR, bootstrap CI, and cross-judge kappa from the artifact."""
    data = json.loads(_find_artifact(cell).read_text(encoding="utf-8"))
    outcomes = data["outcomes"]
    n = len(outcomes)
    successes = sum(int(o["judge_asr"]) for o in outcomes)
    ci = bootstrap_proportion_ci(successes, n)
    return Recomputed(
        n=n,
        asr_pct=round(successes / n * 100),
        ci=(round(ci.lo * 100), round(ci.hi * 100)),
        kappa=float(data["cross_judge_asr_kappa"]),
    )


def _fmt_ci(ci: tuple[int, int]) -> str:
    return f"[{ci[0]}, {ci[1]}]"


def render_tables(rows: list[tuple[Cell, Recomputed]]) -> str:
    """Render the AdvBench and AgentDojo Markdown tables from recomputed rows."""
    out: list[str] = []
    adv = [r for r in rows if r[0].benchmark == "AdvBench"]
    ado = [r for r in rows if r[0].benchmark == "AgentDojo"]

    out.append(f"### AdvBench — direct attacks, n = {adv[0][1].n} per cell\n")
    out.append("| Target | Defence | ASR (judge) | 95% CI | ASR cross-judge κ |")
    out.append("| --- | --- | ---: | --- | ---: |")
    for cell, rc in adv:
        out.append(
            f"| {cell.target} | {cell.defence} | {rc.asr_pct}% | "
            f"{_fmt_ci(rc.ci)} | {rc.kappa:+.3f} |"
        )

    out.append(f"\n### AgentDojo — static indirect injection, n = {ado[0][1].n} per cell\n")
    out.append("| Target | Defence | ASR (judge) | 95% CI | ASR cross-judge κ |")
    out.append("| --- | --- | ---: | --- | ---: |")
    for cell, rc in ado:
        out.append(
            f"| {cell.target} | {cell.defence} | {rc.asr_pct}% | "
            f"{_fmt_ci(rc.ci)} | {rc.kappa:+.3f} |"
        )
    return "\n".join(out)


def check(rows: list[tuple[Cell, Recomputed]]) -> list[str]:
    """Return a list of human-readable drift messages (empty == all match)."""
    drift: list[str] = []
    for cell, rc in rows:
        label = f"{cell.benchmark}/{cell.target}/{cell.defence}"
        if rc.asr_pct != cell.exp_asr_pct:
            drift.append(f"{label}: ASR {rc.asr_pct}% != published {cell.exp_asr_pct}%")
        if rc.ci != cell.exp_ci:
            drift.append(f"{label}: CI {_fmt_ci(rc.ci)} != published {_fmt_ci(cell.exp_ci)}")
        if abs(rc.kappa - cell.exp_kappa) > 1e-9:
            drift.append(f"{label}: κ {rc.kappa:+.3f} != published {cell.exp_kappa:+.3f}")
    return drift


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="assert every recomputed number matches METHODOLOGY.md section 8",
    )
    args = parser.parse_args()

    # The tables use the κ glyph; force UTF-8 so this prints on a cp1252 console.
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")

    try:
        rows = [(cell, recompute(cell)) for cell in CELLS]
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(render_tables(rows))

    if args.check:
        drift = check(rows)
        if drift:
            print("\nDRIFT vs METHODOLOGY.md section 8:", file=sys.stderr)
            for msg in drift:
                print(f"  - {msg}", file=sys.stderr)
            return 1
        print("\nok: all 12 cells match the frozen numbers in METHODOLOGY.md section 8.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
