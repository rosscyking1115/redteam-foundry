"""Export a RunResult to a UK AISI Inspect AI eval log.

One-way adapter: a redteam ``RunResult`` becomes an ``inspect_ai`` ``EvalLog``,
written with Inspect's own ``write_eval_log()``. Building the log from
Inspect's real Pydantic classes (rather than hand-rolled JSON) keeps the
output schema-valid by construction and resilient to Inspect version bumps.

The point: anyone using Inspect -- notably the UK AI Security Institute,
whose evaluation framework this is -- can open any run produced by this
harness in ``inspect view``, or load it with ``read_eval_log()``.

``inspect_ai`` is an optional dependency (the ``[inspect]`` extra). Every
import of it is deferred so the core harness never hard-depends on it.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from redteam.orchestrator import CaseOutcome, RunResult

if TYPE_CHECKING:
    from inspect_ai.log import EvalLog, EvalSample

__all__ = ["export_inspect_log", "run_result_to_eval_log"]

# Inspect's ModelOutput.from_content accepts this fixed set of stop reasons.
_StopReason = Literal[
    "stop", "max_tokens", "model_length", "tool_calls", "content_filter", "unknown"
]

# Map the finish_reason strings our target adapters emit (Anthropic, Ollama,
# OpenAI) onto Inspect's vocabulary.
_STOP_REASON_MAP: dict[str, _StopReason] = {
    "end_turn": "stop",
    "stop": "stop",
    "stop_sequence": "stop",
    "eos": "stop",
    "max_tokens": "max_tokens",
    "length": "max_tokens",
    "model_length": "model_length",
    "tool_use": "tool_calls",
    "tool_calls": "tool_calls",
    "content_filter": "content_filter",
}


def _require_inspect() -> None:
    """Raise a friendly error if the optional ``inspect_ai`` dep is missing."""
    try:
        import inspect_ai  # noqa: F401
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "inspect_ai is not installed. It is an optional dependency; install it with:\n"
            '    uv pip install -e ".[inspect]"'
        ) from exc


def _stop_reason(finish_reason: str | None) -> _StopReason:
    if finish_reason is None:
        return "unknown"
    return _STOP_REASON_MAP.get(finish_reason.lower(), "unknown")


def _primary_asr(outcome: CaseOutcome) -> tuple[int, str, str]:
    """Headline ASR verdict for one case: ``(value, scorer, explanation)``.

    Prefers the LLM-judge verdict; falls back to the rule-based pre-screen
    only when the run has not been judged. Per METHODOLOGY section 6 the
    rule-based layer is a pre-screen, never the source of truth -- so which
    scorer produced the value is always recorded alongside it.
    """
    if outcome.judge_asr is not None:
        return outcome.judge_asr, "llm-judge", outcome.judge_reasoning or ""
    return (
        0 if outcome.is_refusal else 1,
        "rule-based",
        f"rule-based pre-screen (matched_phrase={outcome.matched_phrase!r})",
    )


def _to_sample(outcome: CaseOutcome, target_model: str) -> EvalSample:
    """Convert one CaseOutcome into an Inspect EvalSample."""
    from inspect_ai.log import EvalSample
    from inspect_ai.model import ModelOutput
    from inspect_ai.scorer import Score

    asr_value, scorer, explanation = _primary_asr(outcome)
    score_meta: dict[str, Any] = {
        "scorer": scorer,
        "rule_based_is_refusal": outcome.is_refusal,
        "judge_asr": outcome.judge_asr,
        "judge_refusal": outcome.judge_refusal,
        "judge2_asr": outcome.judge2_asr,
        "judge2_refusal": outcome.judge2_refusal,
    }
    sample_meta: dict[str, Any] = {
        "case_source": outcome.case_source,
        "case_category": outcome.case_category,
        "case_severity": outcome.case_severity,
        "cost_usd": float(outcome.cost_usd),
        "input_tokens": outcome.input_tokens,
        "output_tokens": outcome.output_tokens,
        "latency_ms": outcome.latency_ms,
        "judge_reasoning": outcome.judge_reasoning,
        "judge2_reasoning": outcome.judge2_reasoning,
    }
    return EvalSample(
        id=outcome.case_id,
        epoch=1,
        input=outcome.prompt,
        target="attack should fail -- model resists the adversarial prompt",
        output=ModelOutput.from_content(
            model=target_model,
            content=outcome.response_text,
            stop_reason=_stop_reason(outcome.finish_reason),
        ),
        scores={
            "asr": Score(value=asr_value, explanation=explanation, metadata=score_meta),
        },
        metadata=sample_meta,
    )


def run_result_to_eval_log(run: RunResult) -> EvalLog:
    """Convert a redteam ``RunResult`` into an Inspect ``EvalLog`` object."""
    _require_inspect()
    from inspect_ai.log import (
        EvalConfig,
        EvalDataset,
        EvalLog,
        EvalMetric,
        EvalResults,
        EvalScore,
        EvalSpec,
        EvalStats,
    )

    # Headline ASR + which scorer produced it. The LLM judge is the source of
    # truth; the rule-based pre-screen is only used for an un-judged run.
    if run.judged and run.judge_asr_rate is not None:
        scorer_name = "llm-judge"
        asr_rate: float = run.judge_asr_rate
        ci_lo = run.judge_asr_rate_ci_lo
        ci_hi = run.judge_asr_rate_ci_hi
        refusal_rate = run.judge_refusal_rate
    else:
        scorer_name = "rule-based"
        asr_rate = run.asr
        ci_lo = run.asr_ci_lo
        ci_hi = run.asr_ci_hi
        refusal_rate = run.refusal_rate

    sources = sorted({o.case_source for o in run.outcomes})
    dataset = EvalDataset(
        name="+".join(sources) if sources else "redteam",
        samples=run.cases_total,
        sample_ids=[o.case_id for o in run.outcomes],
    )

    # One consolidated metadata dict. Inspect derives EvalLog.metadata from
    # EvalSpec.metadata on read, so everything that must survive a
    # write -> read round-trip lives on the spec.
    meta: dict[str, Any] = {
        "harness": "redteam-foundry",
        "defences": run.defences,
        "headline_scorer": scorer_name,
        "total_cost_usd": float(run.total_cost_usd),
        "judged": run.judged,
        "judge_model_version": run.judge_model_version,
        "cross_judged": run.cross_judged,
        "judge2_model_version": run.judge2_model_version,
        "cross_judge_asr_kappa": run.cross_judge_asr_kappa,
        "cross_judge_asr_alpha": run.cross_judge_asr_alpha,
        "cross_judge_refusal_kappa": run.cross_judge_refusal_kappa,
        "cross_judge_refusal_alpha": run.cross_judge_refusal_alpha,
    }
    spec = EvalSpec(
        created=run.started_at,
        task=f"redteam/{run.run_name}",
        task_display_name=run.run_name,
        dataset=dataset,
        model=run.target,
        config=EvalConfig(limit=run.cases_total),
        metadata=meta,
    )

    samples = [_to_sample(o, run.target) for o in run.outcomes]

    score_meta: dict[str, Any] = {
        "ci95_lo": ci_lo,
        "ci95_hi": ci_hi,
        "refusal_rate": refusal_rate,
        "note": (
            "ASR is the validated headline metric (METHODOLOGY section 7); "
            "refusal_rate is descriptive only."
        ),
    }
    eval_score = EvalScore(
        name="asr",
        scorer=scorer_name,
        scored_samples=len(samples),
        metrics={"mean": EvalMetric(name="mean", value=float(asr_rate))},
        metadata=score_meta,
    )
    results = EvalResults(
        total_samples=run.cases_total,
        completed_samples=run.cases_total,
        scores=[eval_score],
    )

    return EvalLog(
        eval=spec,
        status="success",
        results=results,
        stats=EvalStats(started_at=run.started_at, completed_at=run.finished_at),
        samples=samples,
        metadata=meta,
    )


def export_inspect_log(
    run: RunResult,
    out_path: Path,
    fmt: Literal["eval", "json", "auto"] = "auto",
) -> Path:
    """Write ``run`` as an Inspect eval log at ``out_path``; return the path."""
    _require_inspect()
    from inspect_ai.log import write_eval_log

    log = run_result_to_eval_log(run)
    write_eval_log(log, str(out_path), format=fmt)
    return out_path
