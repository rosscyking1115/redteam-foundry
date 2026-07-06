"""Defence composition tests — purely structural, no API calls.

Defends: defences compose and wrap a target without changing its send() contract, so stacking them is sound.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest

from redteam.defences.base import Defence, SendLike, merge_system, synthetic_refusal
from redteam.schemas import Message, TargetResponse


class _RecordingTarget:
    """Minimal SendLike that records the args it was called with."""

    id = "recording-target"
    model_version = "stub-1"

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def send(
        self,
        messages: list[Message],
        *,
        system: str | None = None,
        max_tokens: int = 1024,
    ) -> TargetResponse:
        self.calls.append({"messages": messages, "system": system, "max_tokens": max_tokens})
        return TargetResponse(
            target_id=self.id,
            model_version=self.model_version,
            request_messages=messages,
            response_text="OK",
            finish_reason="stop",
            input_tokens=1,
            output_tokens=1,
            cost_usd=Decimal("0"),
            latency_ms=1,
        )


def test_recording_target_satisfies_sendlike_protocol() -> None:
    rt = _RecordingTarget()
    assert isinstance(rt, SendLike)


@pytest.mark.asyncio
async def test_default_defence_is_pass_through() -> None:
    rt = _RecordingTarget()
    d = Defence(rt)
    msgs = [Message(role="user", content="hi")]
    resp = await d.send(msgs, system="be nice", max_tokens=8)
    assert resp.response_text == "OK"
    assert rt.calls == [{"messages": msgs, "system": "be nice", "max_tokens": 8}]


def test_defence_composition_id_chain() -> None:
    class Outer(Defence):
        defence_id = "outer"

    class Inner(Defence):
        defence_id = "inner"

    rt = _RecordingTarget()
    stack = Outer(Inner(rt))
    assert stack.id == "outer+inner+recording-target"
    assert stack.model_version == "stub-1"


def test_merge_system_drops_nones_and_joins() -> None:
    assert merge_system(None, None) is None
    assert merge_system("a") == "a"
    assert merge_system("a", None, "b") == "a\n\nb"
    assert merge_system(None, "x") == "x"


def test_synthetic_refusal_has_zero_cost() -> None:
    msgs = [Message(role="user", content="...")]
    r = synthetic_refusal(
        target_id="x",
        model_version="y",
        request_messages=msgs,
        reason="unsafe input",
        by="LlamaGuard4-pre",
    )
    assert r.response_text.startswith("[REFUSED BY LlamaGuard4-pre]")
    assert r.cost_usd == Decimal("0")
    assert r.input_tokens == 0
    assert r.finish_reason == "refused_by_defence"
