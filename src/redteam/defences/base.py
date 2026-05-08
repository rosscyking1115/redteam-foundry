"""Defence base class — composable wrappers around a Target.

A Defence has the same external `send()` signature as a Target, so any
caller can treat them interchangeably. Defences compose: stack them by
nesting.

Why Defence does NOT inherit from Target
----------------------------------------
Inheritance would re-trigger the Target base class's cache + budget
gates at every wrapper layer, double-counting spend. By keeping Defence
a separate type that *delegates to* an inner SendLike, all cache /
budget bookkeeping happens exactly once at the innermost Target.

Composition
-----------
    target  = AnthropicTarget(cache=...)
    stack   = LlamaGuard4PostFilter(SystemPromptDefence(target), guard=guard_target)
    response = await stack.send([Message(role="user", content="...")])

Each defence's `send()` may modify messages/system before forwarding,
add post-call checks, or short-circuit with a synthetic refusal when
the inner call would have been unsafe.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from redteam.schemas import Message, TargetResponse


@runtime_checkable
class SendLike(Protocol):
    """Anything exposing the Target.send() surface — Target or another Defence."""

    id: str
    model_version: str

    async def send(
        self,
        messages: list[Message],
        *,
        system: str | None = None,
        max_tokens: int = 1024,
    ) -> TargetResponse: ...


class Defence:
    """Base class for defences. Wraps a SendLike and forwards by default.

    Subclasses override `send()` to add defence logic. The simplest form
    modifies `messages` / `system` in place and forwards. More complex
    forms (Llama Guard) make their own classification call first and may
    short-circuit with a synthetic refusal.
    """

    # Stable id used in TargetResponse.target_id. Subclasses should set
    # this to a defence-prefixed id like "system-prompt+claude-sonnet-4-6".
    defence_id: str = "passthrough"

    def __init__(self, inner: SendLike) -> None:
        self._inner = inner
        self.id = f"{self.defence_id}+{inner.id}"
        self.model_version = inner.model_version

    async def send(
        self,
        messages: list[Message],
        *,
        system: str | None = None,
        max_tokens: int = 1024,
    ) -> TargetResponse:
        """Default: pure pass-through. Subclasses override."""
        return await self._inner.send(messages, system=system, max_tokens=max_tokens)


def merge_system(*parts: str | None) -> str | None:
    """Concatenate system prompts in order, dropping Nones. Two consecutive
    blank lines between parts so the model sees clear section breaks."""
    kept = [p for p in parts if p]
    if not kept:
        return None
    return "\n\n".join(kept)


def synthetic_refusal(
    *,
    target_id: str,
    model_version: str,
    request_messages: list[Message],
    reason: str,
    by: str,
) -> TargetResponse:
    """Build a TargetResponse that represents a refusal made by a defence
    BEFORE calling the inner target. Used by pre-filters that block unsafe
    input. Cost = 0 (we never actually queried the protected target)."""
    from decimal import Decimal

    return TargetResponse(
        target_id=target_id,
        model_version=model_version,
        request_messages=request_messages,
        response_text=f"[REFUSED BY {by}] {reason}",
        finish_reason="refused_by_defence",
        input_tokens=0,
        output_tokens=0,
        cost_usd=Decimal("0"),
        latency_ms=0,
        attempt=1,
    )
