"""cross_judge_run() integration test with mocked second judge.

Defends: the cross-judge path computes inter-judge agreement (Cohen's kappa /
Krippendorff's alpha) — the headline validation mechanism (§7).
"""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest

from redteam.scorers import JudgeVerdict


def _write_judged_skeleton(
    path: Path, n: int = 4, model: str = "claude-haiku-4-5-20251001"
) -> None:
    payload = {
        "run_name": "fixture-judged",
        "target": "claude-sonnet-4-6",
        "defences": [],
        "cases_total": n,
        "refusals": 0,
        "asr": 0.0,
        "refusal_rate": 0.0,
        "total_cost_usd": "0",
        "started_at": "2026-05-09T00:00:00+00:00",
        "finished_at": "2026-05-09T00:00:01+00:00",
        "judged": True,
        "judge_model_version": model,
        "judge_asr_rate": 0.0,
        "judge_refusal_rate": 0.5,
        "judge_n_judged": n,
        "judge_n_failed": 0,
        "outcomes": [
            {
                "case_id": f"c-{i}",
                "case_source": "advbench",
                "case_category": "harmful_content",
                "case_severity": "high",
                "prompt": f"prompt {i}",
                "response_text": f"resp {i}",
                "finish_reason": "stop",
                "is_refusal": False,
                "matched_phrase": None,
                "cost_usd": "0",
                "input_tokens": 1,
                "output_tokens": 1,
                "latency_ms": 1,
                "judge_asr": 0,
                "judge_refusal": 1 if i % 2 == 0 else 0,
                "judge_confidence": 0.9,
                "judge_reasoning": "ok",
            }
            for i in range(n)
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


@pytest.mark.asyncio
async def test_cross_judge_writes_agreement(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    from redteam.orchestrator import cross_judge_run
    from redteam.scorers import judge_claude

    run = tmp_path / "run.judged.json"
    _write_judged_skeleton(run, n=4)

    # Make judge2 perfectly mirror judge1 -> kappa=1.0, alpha=1.0
    async def fake_judge(self: object, *, prompt: str, response_text: str) -> JudgeVerdict:
        i = int(prompt.rsplit(" ", 1)[-1])
        return JudgeVerdict(
            asr=0,
            refusal=1 if i % 2 == 0 else 0,
            confidence=0.85,
            reasoning="cross-judge",
        )

    monkeypatch.setattr(judge_claude.ClaudeJudge, "judge", fake_judge)
    from anthropic import AsyncAnthropic

    monkeypatch.setattr(AsyncAnthropic, "__init__", lambda self, **kw: None)

    scored = await cross_judge_run(
        run, judge2_model="claude-sonnet-4-6", cache_root=tmp_path, budget_usd=Decimal("1.00")
    )
    assert scored.cross_judged is True
    assert scored.judge2_model_version == "claude-sonnet-4-6"
    assert scored.judge2_n_judged == 4
    assert scored.judge2_n_failed == 0
    # Perfect agreement on both axes since fake_judge mirrors judge1
    assert scored.cross_judge_agreement_n == 4
    assert scored.cross_judge_asr_kappa == pytest.approx(1.0)
    assert scored.cross_judge_asr_alpha == pytest.approx(1.0)
    assert scored.cross_judge_refusal_kappa == pytest.approx(1.0)
    assert scored.cross_judge_refusal_alpha == pytest.approx(1.0)


@pytest.mark.asyncio
async def test_cross_judge_rejects_same_model(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    from redteam.orchestrator import cross_judge_run

    run = tmp_path / "run.judged.json"
    _write_judged_skeleton(run, n=2, model="claude-haiku-4-5-20251001")

    from anthropic import AsyncAnthropic

    monkeypatch.setattr(AsyncAnthropic, "__init__", lambda self, **kw: None)

    with pytest.raises(ValueError, match="matches judge1"):
        await cross_judge_run(
            run,
            judge2_model="claude-haiku-4-5-20251001",
            cache_root=tmp_path,
            budget_usd=Decimal("1.00"),
        )


@pytest.mark.asyncio
async def test_cross_judge_requires_judged_input(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    from redteam.orchestrator import cross_judge_run

    # Skeleton without "judged": True
    run = tmp_path / "run.json"
    payload = {
        "run_name": "x",
        "target": "claude-sonnet-4-6",
        "defences": [],
        "cases_total": 0,
        "refusals": 0,
        "asr": 0.0,
        "refusal_rate": 0.0,
        "total_cost_usd": "0",
        "started_at": "2026-05-09T00:00:00+00:00",
        "finished_at": "2026-05-09T00:00:01+00:00",
        "outcomes": [],
    }
    run.write_text(json.dumps(payload), encoding="utf-8")

    from anthropic import AsyncAnthropic

    monkeypatch.setattr(AsyncAnthropic, "__init__", lambda self, **kw: None)

    with pytest.raises(ValueError, match="not been judged"):
        await cross_judge_run(
            run,
            judge2_model="claude-sonnet-4-6",
            cache_root=tmp_path,
            budget_usd=Decimal("1.00"),
        )
