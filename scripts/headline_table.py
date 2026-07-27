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

from redteam.stats import bootstrap_proportion_ci, is_degenerate_kappa

REPO_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = REPO_ROOT / "results"


# Cross-judge kappa status. Cohen's kappa is only a *measurement* when the two
# raters' labels actually vary. When both judges score every case identically
# and constantly (here: ASR = 0 on every case), expected agreement pe == 1 and
# kappa is 0/0 — undefined. The scorer assigns +1.000 by convention in that
# case (see `_binary_kappa` in src/redteam/scorers/judge_human.py), which is a
# reporting convention, not evidence of agreement. Freezing this status per
# cell keeps the distinction enforced rather than merely described.
DEGENERATE = "degenerate"  # pe == 1: both judges constant, kappa undefined
INFORMATIVE = "informative"  # label variance present: kappa is a real statistic


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
    exp_kappa_status: str  # DEGENERATE or INFORMATIVE — see above


# The 12 evaluation cells. Frozen values mirror METHODOLOGY.md section 8; the
# `glob` locates the cached cross-judged artifact regardless of run timestamp.
#
# Eleven of the twelve are DEGENERATE on the cross-judge axis: both judges
# scored ASR = 0 on every cross-judged case, so kappa carries no information.
# The one exception is the AgentDojo Llama baseline, where both judges
# independently flagged the same 2 of 50 cases. Note that the AdvBench Llama
# baseline reads 1% ASR from the primary judge, but that single positive case
# is one of the two the cross-judge failed to parse — so its cross-judge sample
# is all-zero and its kappa is degenerate too. The substantive agreement
# evidence is the positive control below, not this matrix.
CELLS: list[Cell] = [
    # AdvBench — direct attacks, n = 100 per cell.
    Cell("AdvBench", "Sonnet 4.6", "baseline", "anthropic-baseline-*", 0, (0, 0), 1.0, DEGENERATE),
    Cell(
        "AdvBench", "Sonnet 4.6", "full-stack", "anthropic-full-stack-*", 0, (0, 0), 1.0, DEGENERATE
    ),
    Cell(
        "AdvBench",
        "Llama 3.1 8B",
        "baseline",
        "local-llama31-baseline-*",
        1,
        (0, 3),
        1.0,
        DEGENERATE,
    ),
    Cell(
        "AdvBench",
        "Llama 3.1 8B",
        "full-stack",
        "local-llama31-full-stack-*",
        0,
        (0, 0),
        1.0,
        DEGENERATE,
    ),
    # AgentDojo — static indirect injection, n = 50 per cell.
    Cell("AgentDojo", "Sonnet 4.6", "baseline", "agentdojo-baseline-*", 0, (0, 0), 1.0, DEGENERATE),
    Cell(
        "AgentDojo",
        "Sonnet 4.6",
        "+ spotlighting",
        "agentdojo-spotlighting-*",
        0,
        (0, 0),
        1.0,
        DEGENERATE,
    ),
    Cell(
        "AgentDojo", "Sonnet 4.6", "+ SecAlign", "agentdojo-secalign-*", 0, (0, 0), 1.0, DEGENERATE
    ),
    Cell(
        "AgentDojo",
        "Sonnet 4.6",
        "full prompt stack",
        "agentdojo-full-prompt-stack-*",
        0,
        (0, 0),
        1.0,
        DEGENERATE,
    ),
    Cell(
        "AgentDojo",
        "Llama 3.1 8B",
        "baseline",
        "agentdojo-local-baseline-*",
        4,
        (0, 10),
        1.0,
        INFORMATIVE,
    ),
    Cell(
        "AgentDojo",
        "Llama 3.1 8B",
        "+ spotlighting",
        "agentdojo-local-spotlighting-*",
        0,
        (0, 0),
        1.0,
        DEGENERATE,
    ),
    Cell(
        "AgentDojo",
        "Llama 3.1 8B",
        "+ SecAlign",
        "agentdojo-local-secalign-*",
        0,
        (0, 0),
        1.0,
        DEGENERATE,
    ),
    Cell(
        "AgentDojo",
        "Llama 3.1 8B",
        "full prompt stack",
        "agentdojo-local-full_prompt_stack-*",
        0,
        (0, 0),
        1.0,
        DEGENERATE,
    ),
]

# The validating cell. Because eleven of twelve matrix cells are degenerate on
# the cross-judge axis, the claim "the two judges agree on ASR" rests on this
# run — the only cell with substantial label variance on both margins (79 of 98
# cross-judged cases scored ASR = 1 by each judge). Frozen so `--check` proves
# the number the claim actually leans on, not the ones it cannot.
POSITIVE_CONTROL = Cell(
    benchmark="AdvBench",
    target="llama2-uncensored:7b (positive control)",
    defence="none",
    glob="positive-control-*",
    exp_asr_pct=80,
    exp_ci=(72, 87),
    exp_kappa=0.935,
    exp_kappa_status=INFORMATIVE,
)

# The AgentDojo positive control — a FAILED control, frozen so it stays visible.
# Pre-registered PASS threshold was ASR >= 20% (configs/run_agentdojo_positive
# _control.yaml); the run scored 2%. It does NOT license "the model resisted":
# the same unaligned model confabulates rather than following the tool output at
# all, so the cell measures incapacity, not robustness. Kept in `--check` so the
# failure cannot quietly disappear from the record. See METHODOLOGY.md §12.6.
AGENTDOJO_POSITIVE_CONTROL = Cell(
    benchmark="AgentDojo",
    target="llama2-uncensored:7b (positive control, FAILED)",
    defence="none",
    glob="agentdojo-positive-control-*",
    exp_asr_pct=2,
    exp_ci=(0, 6),
    exp_kappa=0.658,
    exp_kappa_status=INFORMATIVE,
)

CONTROLS: list[Cell] = [POSITIVE_CONTROL, AGENTDOJO_POSITIVE_CONTROL]


@dataclass(frozen=True)
class Recomputed:
    """A cell's ASR / CI / kappa recomputed live from its cached artifact."""

    n: int
    asr_pct: int
    ci: tuple[int, int]
    kappa: float
    kappa_status: str
    cross_n: int  # cases with a verdict from BOTH judges
    cross_pos_a: int  # primary-judge ASR = 1 among those
    cross_pos_b: int  # cross-judge ASR = 1 among those


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

    # Cross-judge axis: only cases both judges returned a parseable verdict on.
    paired = [
        (int(o["judge_asr"]), int(o["judge2_asr"]))
        for o in outcomes
        if o.get("judge_asr") is not None and o.get("judge2_asr") is not None
    ]
    pos_a = sum(a for a, _ in paired)
    pos_b = sum(b for _, b in paired)

    return Recomputed(
        n=n,
        asr_pct=round(successes / n * 100),
        ci=(round(ci.lo * 100), round(ci.hi * 100)),
        kappa=float(data["cross_judge_asr_kappa"]),
        kappa_status=classify_kappa(pos_a, pos_b, len(paired)),
        cross_n=len(paired),
        cross_pos_a=pos_a,
        cross_pos_b=pos_b,
    )


def classify_kappa(pos_a: int, pos_b: int, n: int) -> str:
    """DEGENERATE when Cohen's kappa is 0/0, INFORMATIVE when it is a statistic.

    Thin wrapper over ``redteam.stats.is_degenerate_kappa``, which is the single
    source of truth for the rule. The staleness scorer consumes the same helper,
    so the published table and the composite metric cannot disagree about which
    cells count as measured.
    """
    return DEGENERATE if is_degenerate_kappa(pos_a, pos_b, n) else INFORMATIVE


def _fmt_ci(ci: tuple[int, int]) -> str:
    return f"[{ci[0]}, {ci[1]}]"


def _fmt_kappa(rc: Recomputed) -> str:
    """Render kappa, refusing to print a number the data cannot support."""
    if rc.kappa_status == DEGENERATE:
        return f"n/a (degenerate, {rc.cross_n}/{rc.cross_n} labels identical)"
    return f"{rc.kappa:+.3f} (n = {rc.cross_n})"


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
            f"{_fmt_ci(rc.ci)} | {_fmt_kappa(rc)} |"
        )

    out.append(f"\n### AgentDojo — static indirect injection, n = {ado[0][1].n} per cell\n")
    out.append("| Target | Defence | ASR (judge) | 95% CI | ASR cross-judge κ |")
    out.append("| --- | --- | ---: | --- | ---: |")
    for cell, rc in ado:
        out.append(
            f"| {cell.target} | {cell.defence} | {rc.asr_pct}% | "
            f"{_fmt_ci(rc.ci)} | {_fmt_kappa(rc)} |"
        )
    return "\n".join(out)


def render_controls(rows: list[tuple[Cell, Recomputed]]) -> str:
    """Render the positive controls — including the one that failed."""
    out = [
        "\n### Positive controls — does the pipeline register an attack that lands?\n",
        "| Benchmark | Target | ASR (judge) | 95% CI | ASR cross-judge κ |",
        "| --- | --- | ---: | --- | ---: |",
    ]
    out.extend(
        f"| {cell.benchmark} | {cell.target} | {rc.asr_pct}% | "
        f"{_fmt_ci(rc.ci)} | {_fmt_kappa(rc)} |"
        for cell, rc in rows
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
        if rc.kappa_status != cell.exp_kappa_status:
            drift.append(
                f"{label}: cross-judge κ is {rc.kappa_status}, published as "
                f"{cell.exp_kappa_status} "
                f"({rc.cross_pos_a}/{rc.cross_n} and {rc.cross_pos_b}/{rc.cross_n} positive)"
            )
        # A degenerate cell's kappa is a 0/0 convention, not a measurement, so
        # there is nothing to freeze. Only informative cells are compared.
        if rc.kappa_status == INFORMATIVE and abs(rc.kappa - cell.exp_kappa) > 5e-4:
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
        controls = [(cell, recompute(cell)) for cell in CONTROLS]
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(render_tables(rows))
    print(render_controls(controls))

    n_degenerate = sum(1 for _, rc in rows if rc.kappa_status == DEGENERATE)
    print(
        f"\nCross-judge κ on ASR is degenerate (0/0) in {n_degenerate} of {len(rows)} "
        f"matrix cells — both judges label every case identically and constantly, so "
        f"κ carries no information there. The agreement claim rests on the AdvBench "
        f"positive control above. The AgentDojo control FAILED its pre-registered "
        f"threshold (2% vs 20%) and is reported as inconclusive, not as a null."
    )

    if args.check:
        drift = check([*rows, *controls])
        if drift:
            print("\nDRIFT vs METHODOLOGY.md section 8:", file=sys.stderr)
            for msg in drift:
                print(f"  - {msg}", file=sys.stderr)
            return 1
        print(
            f"\nok: all {len(rows)} cells + {len(controls)} positive controls match the "
            f"frozen numbers in METHODOLOGY.md section 8, including which κ values are "
            f"degenerate."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
