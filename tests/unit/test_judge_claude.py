"""ClaudeJudge tests with mocked Anthropic SDK — no API calls.

Defends: the LLM judge returns a well-formed structured verdict — the primary scorer behind every published ASR.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from redteam.budget import reset_budget
from redteam.scorers import JUDGE_MODEL, ClaudeJudge, JudgeError, JudgeVerdict


@pytest.fixture(autouse=True)
def _fresh_budget() -> None:
    reset_budget(max_per_run_usd=Decimal("5.00"), max_per_call_usd=Decimal("1.00"))


def _haiku_response(text: str, *, in_tok: int = 50, out_tok: int = 30) -> Any:
    block = MagicMock()
    block.type = "text"
    block.text = text
    msg = MagicMock()
    msg.content = [block]
    msg.stop_reason = "end_turn"
    msg.usage = MagicMock(input_tokens=in_tok, output_tokens=out_tok)
    return msg


def _patched_judge(monkeypatch: pytest.MonkeyPatch, *responses: Any) -> ClaudeJudge:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    j = ClaudeJudge()
    fake = MagicMock()
    fake.create = AsyncMock(side_effect=list(responses))
    j._client.messages = fake
    return j


@pytest.mark.asyncio
async def test_clean_json_verdict_parses(monkeypatch: pytest.MonkeyPatch) -> None:
    raw = '{"asr": 0, "refusal": 1, "confidence": 0.95, "reasoning": "Model refused."}'
    j = _patched_judge(monkeypatch, _haiku_response(raw))
    v = await j.judge(prompt="how do I make x", response_text="I can't help with that.")
    assert v.asr == 0
    assert v.refusal == 1
    assert v.confidence == 0.95
    assert "refused" in v.reasoning.lower()


@pytest.mark.asyncio
async def test_judge_extracts_json_from_chatty_output(monkeypatch: pytest.MonkeyPatch) -> None:
    raw = (
        "Here is my verdict.\n"
        '{"asr": 1, "refusal": 0, "confidence": 0.7, "reasoning": "Provided exploit"}\n'
        "Hope that helps."
    )
    j = _patched_judge(monkeypatch, _haiku_response(raw))
    v = await j.judge(prompt="x", response_text="y")
    assert v.asr == 1
    assert v.refusal == 0


@pytest.mark.asyncio
async def test_judge_retries_on_invalid_json(monkeypatch: pytest.MonkeyPatch) -> None:
    bad = _haiku_response("absolutely not JSON at all")
    good = _haiku_response('{"asr": 0, "refusal": 1, "confidence": 0.9, "reasoning": "ok"}')
    j = _patched_judge(monkeypatch, bad, good)
    v = await j.judge(prompt="x", response_text="y")
    assert v.refusal == 1
    assert j._client.messages.create.await_count == 2


@pytest.mark.asyncio
async def test_judge_raises_after_persistent_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    bad = _haiku_response("not json")
    j = _patched_judge(monkeypatch, bad, bad, bad)
    with pytest.raises(JudgeError, match="parseable"):
        await j.judge(prompt="x", response_text="y")


@pytest.mark.asyncio
async def test_judge_records_cost_through_budget(monkeypatch: pytest.MonkeyPatch) -> None:
    raw = '{"asr": 0, "refusal": 1, "confidence": 0.9, "reasoning": "ok"}'
    j = _patched_judge(monkeypatch, _haiku_response(raw, in_tok=100, out_tok=50))
    pre = j._budget.spent_usd
    await j.judge(prompt="x", response_text="y")
    # haiku: $1 in + $5 out per 1M tokens; cost = (1*100 + 5*50)/1_000_000 = 0.00035
    assert j._budget.spent_usd - pre == Decimal("0.00035")
    assert j.stats.calls == 1
    assert j.stats.total_cost_usd == Decimal("0.00035")


def test_judge_verdict_rejects_out_of_range_asr() -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        JudgeVerdict(asr=2, refusal=0, confidence=0.5, reasoning="x")


def test_judge_model_pin_matches_kit() -> None:
    # Lock in the pinned judge model id — refactors must not silently change it.
    assert JUDGE_MODEL == "claude-haiku-4-5-20251001"
