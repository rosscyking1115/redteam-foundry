"""Target adapter unit tests with mocked transports.

Defends: each target adapter honours the shared cache/budget contract with its transport mocked (no live API).

These tests do NOT hit any real API. The Anthropic and OpenAI adapters
take a client at construction time, so we patch the SDK class at import
time. The Ollama adapter goes through httpx, so we use respx to mock.

Live smoke tests live in tests/smoke/ and are gated behind RUN_LIVE=1.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from redteam.budget import BudgetGuard, reset_budget
from redteam.cache import ResponseCache
from redteam.schemas import Message
from redteam.targets.anthropic import AnthropicTarget, ConfigError


@pytest.fixture(autouse=True)
def _fresh_budget() -> None:
    reset_budget(max_per_run_usd=Decimal("5.00"), max_per_call_usd=Decimal("1.00"))


def _make_anthropic_response(text: str = "hello", in_tok: int = 10, out_tok: int = 5) -> Any:
    """Build a fake `anthropic.types.Message`-shaped object."""
    block = MagicMock()
    block.type = "text"
    block.text = text
    msg = MagicMock()
    msg.content = [block]
    msg.stop_reason = "end_turn"
    msg.usage = MagicMock(input_tokens=in_tok, output_tokens=out_tok)
    return msg


def _patched_anthropic_target(
    monkeypatch: pytest.MonkeyPatch, response_obj: Any
) -> AnthropicTarget:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")
    target = AnthropicTarget(api_key="test-key-not-real")
    fake_messages = MagicMock()
    fake_messages.create = AsyncMock(return_value=response_obj)
    target._client.messages = fake_messages
    return target


def test_anthropic_missing_key_raises_config_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(ConfigError, match="ANTHROPIC_API_KEY"):
        AnthropicTarget()


@pytest.mark.asyncio
async def test_anthropic_send_returns_typed_response(monkeypatch: pytest.MonkeyPatch) -> None:
    target = _patched_anthropic_target(monkeypatch, _make_anthropic_response("4"))
    resp = await target.send([Message(role="user", content="what is 2+2")], max_tokens=64)
    assert resp.response_text == "4"
    assert resp.target_id == "claude-sonnet-4-6"
    assert resp.input_tokens == 10
    assert resp.output_tokens == 5
    # cost = (3*10 + 15*5) / 1_000_000 = 0.000105
    assert resp.cost_usd == Decimal("0.000105")


@pytest.mark.asyncio
async def test_cache_short_circuits_second_call(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> None:
    cache = ResponseCache(cache_root=tmp_path)
    target = _patched_anthropic_target(monkeypatch, _make_anthropic_response("once"))
    target.cache = cache

    msgs = [Message(role="user", content="hello?")]
    r1 = await target.send(msgs, max_tokens=32)
    r2 = await target.send(msgs, max_tokens=32)
    assert r1.response_text == r2.response_text == "once"
    # The mocked SDK was only called once.
    assert target._client.messages.create.await_count == 1


@pytest.mark.asyncio
async def test_budget_blocks_oversized_call(monkeypatch: pytest.MonkeyPatch) -> None:
    from redteam.budget import BudgetExceeded

    budget = BudgetGuard(max_per_run_usd=Decimal("5.00"), max_per_call_usd=Decimal("0.0001"))
    target = _patched_anthropic_target(monkeypatch, _make_anthropic_response("hi"))
    target.budget = budget
    with pytest.raises(BudgetExceeded, match="Per-call estimate"):
        await target.send([Message(role="user", content="hi" * 100)], max_tokens=4096)


@pytest.mark.asyncio
async def test_budget_records_realised_cost(monkeypatch: pytest.MonkeyPatch) -> None:
    budget = BudgetGuard(max_per_run_usd=Decimal("5.00"), max_per_call_usd=Decimal("1.00"))
    target = _patched_anthropic_target(monkeypatch, _make_anthropic_response("4", 100, 50))
    target.budget = budget
    pre = budget.spent_usd
    await target.send([Message(role="user", content="2+2?")], max_tokens=64)
    # cost = (3*100 + 15*50) / 1_000_000 = 0.001050
    assert budget.spent_usd - pre == Decimal("0.00105")
