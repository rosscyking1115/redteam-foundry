"""Defence comparison + safe-usefulness tests (Phase 3)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from redteam.compare import (
    compare_defences,
    effective_asr,
    frr_from_run,
    render_defence_comparison,
)
from redteam.orchestrator import RunResult


def _run(
    target: str,
    defences: list[str],
    *,
    asr: float = 0.0,
    refusal_rate: float = 0.0,
    judged: bool = False,
    judge_asr: float | None = None,
    judge_refusal: float | None = None,
    cost: str = "0",
) -> RunResult:
    return RunResult(
        run_name="r",
        target=target,
        defences=defences,
        cases_total=50,
        refusals=round(refusal_rate * 50),
        asr=asr,
        refusal_rate=refusal_rate,
        total_cost_usd=Decimal(cost),
        started_at="2026-07-01T00:00:00+00:00",
        finished_at="2026-07-01T00:00:01+00:00",
        outcomes=[],
        judged=judged,
        judge_asr_rate=judge_asr,
        judge_refusal_rate=judge_refusal,
    )


def test_effective_asr_prefers_judge() -> None:
    assert effective_asr(_run("m", [], asr=0.9, judged=True, judge_asr=0.1)) == (0.1, "judge")
    assert effective_asr(_run("m", [], asr=0.9)) == (0.9, "rule-based")


def test_frr_prefers_judge_refusal() -> None:
    r = _run("m", [], refusal_rate=0.4, judged=True, judge_refusal=0.2)
    assert frr_from_run(r) == (0.2, "judge")
    assert frr_from_run(_run("m", [], refusal_rate=0.4)) == (0.4, "rule-based")


def test_compare_without_benign_leaves_frr_undefined() -> None:
    report = compare_defences([_run("m", [], asr=0.05)])
    assert report.n_configs_with_frr == 0
    row = report.rows[0]
    assert row.asr == 0.05
    assert row.frr is None
    assert row.safe_usefulness is None


def test_compare_matches_benign_and_computes_safe_usefulness() -> None:
    adversarial = [_run("m", [], asr=0.0)]
    benign = [_run("m", [], refusal_rate=0.10)]  # 10% false refusals
    report = compare_defences(adversarial, benign)
    row = report.rows[0]
    assert row.frr == pytest.approx(0.10)
    # safe_usefulness = (1 - 0.0) * (1 - 0.10) = 0.90
    assert row.safe_usefulness == pytest.approx(0.90)
    assert report.n_configs_with_frr == 1


def test_over_blocking_defence_scores_worse_on_safe_usefulness() -> None:
    # Two configs, same 0% ASR, but the defended one over-refuses benign prompts.
    adversarial = [_run("m", [], asr=0.0), _run("m", ["system_prompt"], asr=0.0)]
    benign = [
        _run("m", [], refusal_rate=0.02),
        _run("m", ["system_prompt"], refusal_rate=0.40),  # over-blocks
    ]
    report = compare_defences(adversarial, benign)
    by_label = {r.label: r for r in report.rows}
    assert by_label["baseline"].safe_usefulness > by_label["system_prompt"].safe_usefulness


def test_benign_matched_by_config_not_globally() -> None:
    # A benign run for a different config must not populate FRR for this one.
    adversarial = [_run("m", ["secalign"], asr=0.0)]
    benign = [_run("m", [], refusal_rate=0.1)]  # baseline benign, different config
    report = compare_defences(adversarial, benign)
    assert report.rows[0].frr is None


def test_render_is_markdown() -> None:
    md = render_defence_comparison(compare_defences([_run("m", [], asr=0.0)]))
    assert md.startswith("# Defence comparison")
    assert "safe-usefulness" in md
