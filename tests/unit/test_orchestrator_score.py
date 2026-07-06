"""Test the score_run orchestrator path with a mocked judge.

Defends: the scoring path applies the judge to a run and aggregates its verdicts into run-level ASR.
"""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest

from redteam.scorers import JudgeVerdict


def _write_scored_run_skeleton(path: Path, n: int = 3) -> None:
    payload = {
        "run_name": "fixture",
        "target": "claude-sonnet-4-6",
        "defences": [],
        "cases_total": n,
        "refusals": 0,
        "asr": 0.0,
        "refusal_rate": 0.0,
        "total_cost_usd": "0",
        "started_at": "2026-05-09T00:00:00+00:00",
        "finished_at": "2026-05-09T00:00:01+00:00",
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
            }
            for i in range(n)
        ],
    }
    path.write_text(json.dumps(payload))


@pytest.mark.asyncio
async def test_score_run_writes_judged_json(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    from redteam.orchestrator import score_run

    run = tmp_path / "run.json"
    _write_scored_run_skeleton(run, n=3)

    # Patch ClaudeJudge.judge to return a deterministic verdict.
    from redteam.scorers import judge_claude

    async def fake_judge(self: object, *, prompt: str, response_text: str) -> JudgeVerdict:
        # Make response 0 a clean refusal; 1 a redirect; 2 a compliance.
        idx = int(prompt.rsplit(" ", 1)[-1])
        return JudgeVerdict(
            asr=(0 if idx < 2 else 1),
            refusal=(1 if idx == 0 else 0),
            confidence=0.9,
            reasoning=f"verdict for {idx}",
        )

    monkeypatch.setattr(judge_claude.ClaudeJudge, "judge", fake_judge)

    # Stub out the underlying Haiku call so __init__ doesn't fail on a real client.
    from anthropic import AsyncAnthropic

    monkeypatch.setattr(AsyncAnthropic, "__init__", lambda self, **kw: None)

    scored = await score_run(run, cache_root=tmp_path, budget_usd=Decimal("1.00"))
    assert scored.judged is True
    assert scored.judge_n_judged == 3
    assert scored.judge_n_failed == 0
    assert scored.judge_asr_rate == pytest.approx(1 / 3)
    assert scored.judge_refusal_rate == pytest.approx(1 / 3)
    # Output file written next to input
    out = tmp_path / "run.judged.json"
    assert out.exists()
    assert "judge_asr" in out.read_text()


def test_runresult_loads_phase3_jsons_unchanged(tmp_path: Path) -> None:
    """Backward compat: a Phase-3 RunResult JSON without judge fields must
    still validate against the extended schema (defaults fill in)."""
    from redteam.orchestrator import RunResult

    raw = {
        "run_name": "old",
        "target": "claude-sonnet-4-6",
        "defences": [],
        "cases_total": 0,
        "refusals": 0,
        "asr": 0.0,
        "refusal_rate": 0.0,
        "total_cost_usd": "0",
        "started_at": "2026-05-08T00:00:00+00:00",
        "finished_at": "2026-05-08T00:00:01+00:00",
        "outcomes": [],
    }
    r = RunResult.model_validate(raw)
    assert r.judged is False
    assert r.judge_model_version is None
