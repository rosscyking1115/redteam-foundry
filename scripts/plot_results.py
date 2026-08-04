"""Regenerate the README results figure (``docs/results_matrix.png``).

Renders attack-success rate (ASR) across all 12 evaluation cells -- two
models x two benchmarks x defence configs -- as a point-estimate + 95%
bootstrap-CI plot. The numbers mirror ``METHODOLOGY.md`` section 8: LLM-judge
scored (Claude Haiku 4.5), cross-judged by Claude Sonnet 4.6. They are the
published, frozen result; update them here only when ``METHODOLOGY.md``
section 8 changes.

The caption is a published claim in its own right -- it travels to GitHub and
to the PyPI project page -- so it is defined here as ``CAPTION``, embedded in
the PNG's ``Description`` metadata, and guarded by
``tests/unit/test_figure_caption.py``.

Run from the repo root:

    python scripts/plot_results.py

``matplotlib`` is a dev-only dependency (install via the ``[dev]`` extra).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.axes import Axes


@dataclass(frozen=True)
class Cell:
    """One evaluation cell: a (model, defence) pair and its judged ASR."""

    model: str
    defence: str
    asr: float  # judge ASR, percent
    ci_lo: float  # 95% bootstrap CI lower bound, percent
    ci_hi: float  # 95% bootstrap CI upper bound, percent


# Verified judge ASR -- mirrors METHODOLOGY.md section 8.
ADVBENCH: list[Cell] = [
    Cell("Sonnet 4.6", "baseline", 0.0, 0.0, 0.0),
    Cell("Sonnet 4.6", "full-stack", 0.0, 0.0, 0.0),
    Cell("Llama 3.1 8B", "baseline", 1.0, 0.0, 3.0),
    Cell("Llama 3.1 8B", "full-stack", 0.0, 0.0, 0.0),
]
AGENTDOJO: list[Cell] = [
    Cell("Sonnet 4.6", "baseline", 0.0, 0.0, 0.0),
    Cell("Sonnet 4.6", "+ spotlighting", 0.0, 0.0, 0.0),
    Cell("Sonnet 4.6", "+ SecAlign", 0.0, 0.0, 0.0),
    Cell("Sonnet 4.6", "full prompt stack", 0.0, 0.0, 0.0),
    Cell("Llama 3.1 8B", "baseline", 4.0, 0.0, 10.0),
    Cell("Llama 3.1 8B", "+ spotlighting", 0.0, 0.0, 0.0),
    Cell("Llama 3.1 8B", "+ SecAlign", 0.0, 0.0, 0.0),
    Cell("Llama 3.1 8B", "full prompt stack", 0.0, 0.0, 0.0),
]

_COLOR: dict[str, str] = {"Sonnet 4.6": "#2563eb", "Llama 3.1 8B": "#d97706"}
_OUT = Path(__file__).resolve().parents[1] / "docs" / "results_matrix.png"

# The caption says what is plotted, and stops.
#
# It used to end "two-judge cross-validated (ASR κ = 1.00, all 12 cells)".
# 0.4.0 retracted exactly that claim: in 11 of the 12 cells both judges
# labelled every case identically and constantly, so expected agreement
# pe == 1 and Cohen's κ is an undefined 0/0 that the scorer fills in as
# +1.000 by convention. The figure therefore advertised as cross-validation
# the one thing the project had published a correction against.
#
# The surviving measurement -- the positive control's κ = +0.935, n = 98 --
# is not stated here either, and deliberately. It belongs to a cell that is
# not among the 12 plotted, so in this caption it would read as though the
# matrix had been validated at 0.935. Every judge-agreement figure in this
# project needs a sentence of qualification to be read correctly, and a
# caption is the one place in a document that travels separated from its
# qualification -- a screenshot of this figure carries the caption and
# nothing else. The qualified version lives in README.md, under
# "Why the result is trustworthy, not just low", and in METHODOLOGY.md 7/8.
CAPTION = "Point = LLM-judge ASR; whisker = 95% bootstrap CI."


def _draw_panel(ax: Axes, title: str, cells: list[Cell]) -> None:
    """Draw one benchmark panel as a horizontal point + CI plot."""
    rows = list(enumerate(reversed(cells)))  # first cell ends up at the top
    for y, cell in rows:
        color = _COLOR[cell.model]
        ax.errorbar(
            cell.asr,
            y,
            xerr=[[cell.asr - cell.ci_lo], [cell.ci_hi - cell.asr]],
            fmt="o",
            color=color,
            ecolor=color,
            elinewidth=1.4,
            capsize=3.5,
            markersize=7,
        )
        ax.text(
            cell.ci_hi + 0.35,
            y,
            f"{cell.asr:.0f}%",
            va="center",
            ha="left",
            fontsize=9,
            color="#374151",
        )
    ax.set_yticks([y for y, _ in rows])
    ax.set_yticklabels([f"{c.model}  ·  {c.defence}" for _, c in rows], fontsize=9)
    ax.set_ylim(-0.7, len(cells) - 0.3)
    ax.set_title(title, fontsize=10, fontweight="bold", loc="left", pad=8)
    ax.grid(axis="x", color="#e5e7eb", linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.tick_params(left=False)


def main() -> None:
    """Render the figure and write it to ``docs/results_matrix.png``."""
    plt.switch_backend("Agg")
    fig, (ax_top, ax_bot) = plt.subplots(
        2,
        1,
        figsize=(8.6, 7.0),
        height_ratios=[len(ADVBENCH), len(AGENTDOJO)],
    )
    _draw_panel(ax_top, "AdvBench  —  direct attacks  (n = 100 per cell)", ADVBENCH)
    _draw_panel(
        ax_bot,
        "AgentDojo  —  static indirect injection  (n = 50 per cell)",
        AGENTDOJO,
    )

    for ax in (ax_top, ax_bot):
        ax.set_xlim(-0.5, 12.0)
    ax_bot.set_xlabel("Attack success rate  (%)", fontsize=10)

    fig.suptitle(
        "Attack success rate across 12 evaluation cells",
        fontsize=13,
        fontweight="bold",
        x=0.04,
        ha="left",
    )
    fig.text(0.04, 0.015, CAPTION, fontsize=8, color="#6b7280", ha="left")

    fig.tight_layout(rect=(0.0, 0.04, 1.0, 0.95))
    _OUT.parent.mkdir(parents=True, exist_ok=True)
    # Recorded in the PNG itself so the guard can read what the committed
    # artifact claims, not only what the generator would claim on its next run.
    fig.savefig(_OUT, dpi=200, metadata={"Description": CAPTION})
    print(f"Wrote {_OUT}")


if __name__ == "__main__":
    main()
