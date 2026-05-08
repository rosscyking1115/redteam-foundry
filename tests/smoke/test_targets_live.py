"""Live target smoke tests — gated behind RUN_LIVE=1.

Per Phase 2 acceptance: smoke test sends "What is 2+2?" through each
target and gets a sane response; cost tracking rolls up correctly;
cache hit on second run.

Skipped by default so CI never spends API budget. To run locally:

    $env:RUN_LIVE = "1"          # PowerShell
    pytest tests/smoke -v
    Remove-Item Env:\\RUN_LIVE

    export RUN_LIVE=1            # bash
    pytest tests/smoke -v
    unset RUN_LIVE

Lesson L14: don't run a 200-case live eval from a flaky network. These
smoke tests do ONE call per target. If you want the real eval, run it
in CI's nightly job, not from your laptop.
"""

from __future__ import annotations

import os
from decimal import Decimal
from pathlib import Path

import pytest

from redteam.budget import reset_budget
from redteam.cache import ResponseCache
from redteam.schemas import Message
from redteam.targets import AnthropicTarget, ConfigError, OllamaTarget, OllamaUnavailable

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_LIVE") != "1",
    reason="Live target smoke skipped (set RUN_LIVE=1 to run)",
)


@pytest.mark.asyncio
async def test_anthropic_can_add_two_plus_two(tmp_path: Path) -> None:
    reset_budget(max_per_run_usd=Decimal("0.50"), max_per_call_usd=Decimal("0.20"))
    cache = ResponseCache(cache_root=tmp_path)
    try:
        target = AnthropicTarget(cache=cache)
    except ConfigError as exc:
        pytest.skip(str(exc))

    msgs = [Message(role="user", content="What is 2 + 2? Answer with just the digit.")]
    resp = await target.send(msgs, max_tokens=8)
    assert "4" in resp.response_text
    assert resp.input_tokens > 0
    assert resp.output_tokens > 0
    assert resp.cost_usd > Decimal("0")
    assert resp.latency_ms > 0

    # Second call hits cache: same response, no new spend.
    spent_after_first = target.budget.spent_usd
    resp2 = await target.send(msgs, max_tokens=8)
    assert resp2.response_text == resp.response_text
    assert target.budget.spent_usd == spent_after_first  # cached, no new spend


@pytest.mark.asyncio
async def test_ollama_can_add_two_plus_two(tmp_path: Path) -> None:
    reset_budget(max_per_run_usd=Decimal("1.00"), max_per_call_usd=Decimal("1.00"))
    cache = ResponseCache(cache_root=tmp_path)
    target = OllamaTarget(cache=cache)
    try:
        await target.healthcheck()
    except OllamaUnavailable as exc:
        pytest.skip(str(exc))

    msgs = [Message(role="user", content="What is 2 + 2? Answer with just the digit.")]
    resp = await target.send(msgs, max_tokens=16)
    assert "4" in resp.response_text
    assert resp.input_tokens > 0
    assert resp.output_tokens > 0
    assert resp.cost_usd == Decimal("0")  # local model
    assert resp.latency_ms > 0
