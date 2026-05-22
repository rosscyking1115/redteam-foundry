"""Unit tests for the Inspect AI eval-log exporter (`redteam.inspect_export`).

`inspect_ai` ships in the `[dev]` extra, so the test environment always has
it -- no import guard needed.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from inspect_ai.log import read_eval_log

from redteam.inspect_export import export_inspect_log, run_result_to_eval_log
from redteam.orchestrator import CaseOutcome, RunResult


def _outcome(case_id: str, *, judged: bool) -> CaseOutcome:
    return CaseOutcome(
        case_id=case_id,
        case_source="advbench",
        case_category="harmful_content",
        case_severity="high",
        prompt=f"prompt {case_id}",
        response_text=f"I can't help with that ({case_id}).",
        finish_reason="end_turn",
        is_refusal=True,
        matched_phrase="can't help",
        cost_usd=Decimal("0.001"),
        input_tokens=10,
        output_tokens=8,
        latency_ms=120,
        judge_asr=0 if judged else None,
        judge_refusal=1 if judged else None,
        judge_confidence=0.95 if judged else None,
        judge_reasoning="model refused" if judged else None,
    )


def _run_result(*, judged: bool) -> RunResult:
    outcomes = [_outcome(f"c{i}", judged=judged) for i in range(3)]
    return RunResult(
        run_name="test-run",
        target="claude-sonnet-4-6",
        defences=["system-prompt"],
        cases_total=3,
        refusals=3,
        asr=0.0,
        refusal_rate=1.0,
        total_cost_usd=Decimal("0.003"),
        started_at="2026-05-21T10:00:00+00:00",
        finished_at="2026-05-21T10:01:00+00:00",
        outcomes=outcomes,
        asr_ci_lo=0.0,
        asr_ci_hi=0.0,
        refusal_rate_ci_lo=1.0,
        refusal_rate_ci_hi=1.0,
        judged=judged,
        judge_model_version="claude-haiku-4-5-20251001" if judged else None,
        judge_asr_rate=0.0 if judged else None,
        judge_refusal_rate=1.0 if judged else None,
        judge_total_cost_usd=Decimal("0.002") if judged else None,
        judge_n_judged=3 if judged else None,
        judge_n_failed=0 if judged else None,
        judge_asr_rate_ci_lo=0.0 if judged else None,
        judge_asr_rate_ci_hi=0.0 if judged else None,
        cross_judged=judged,
        judge2_model_version="claude-sonnet-4-6" if judged else None,
        cross_judge_agreement_n=3 if judged else None,
        cross_judge_asr_kappa=1.0 if judged else None,
        cross_judge_asr_alpha=1.0 if judged else None,
        cross_judge_refusal_kappa=1.0 if judged else None,
        cross_judge_refusal_alpha=1.0 if judged else None,
    )


def test_run_result_to_eval_log_structure() -> None:
    log = run_result_to_eval_log(_run_result(judged=True))
    assert log.status == "success"
    assert log.samples is not None
    assert len(log.samples) == 3
    assert log.eval.model == "claude-sonnet-4-6"
    assert log.eval.task == "redteam/test-run"
    # every sample carries the headline ASR score, here 0 (all refused)
    for sample in log.samples:
        scores = sample.scores or {}
        assert "asr" in scores
        assert scores["asr"].value == 0
        assert scores["asr"].metadata is not None
        assert scores["asr"].metadata["scorer"] == "llm-judge"


def test_export_roundtrips_through_read_eval_log(tmp_path: Path) -> None:
    out = tmp_path / "test-run.json"
    export_inspect_log(_run_result(judged=True), out, fmt="json")
    assert out.exists()

    log = read_eval_log(str(out))
    assert log.status == "success"
    assert log.samples is not None
    assert len(log.samples) == 3
    assert log.results is not None
    asr_score = log.results.scores[0]
    assert asr_score.name == "asr"
    assert asr_score.scorer == "llm-judge"
    assert asr_score.metrics["mean"].value == 0.0

    # Cross-judge agreement must survive the write -> read round-trip.
    # Inspect rebuilds EvalLog.metadata from EvalSpec.metadata on read, so
    # this also guards against regressing to top-level-only metadata.
    assert log.eval.metadata is not None
    assert log.eval.metadata["cross_judged"] is True
    assert log.eval.metadata["cross_judge_asr_kappa"] == 1.0


def test_unjudged_run_falls_back_to_rule_based() -> None:
    log = run_result_to_eval_log(_run_result(judged=False))
    assert log.results is not None
    assert log.results.scores[0].scorer == "rule-based"
    # rule-based pre-screen: all three cases refused -> ASR 0
    assert log.samples is not None
    for sample in log.samples:
        scores = sample.scores or {}
        assert scores["asr"].value == 0
        assert scores["asr"].metadata is not None
        assert scores["asr"].metadata["scorer"] == "rule-based"
