"""Anthropic adapter — Claude Sonnet 4.6 via the official SDK.

The SDK has its own retry/backoff (configurable via `max_retries`); we
defer to it instead of layering tenacity on top, which would otherwise
multiply timeouts.

Authentication: reads ANTHROPIC_API_KEY from the environment at __init__
time. Raises ConfigError immediately if the key is missing — no point
deferring to the first call.
"""

from __future__ import annotations

import os
import time
from typing import Any

from anthropic import AsyncAnthropic

from redteam.budget import BudgetGuard
from redteam.cache import ResponseCache
from redteam.schemas import Message, TargetResponse
from redteam.targets._pricing import cost_for
from redteam.targets.base import Target


class ConfigError(RuntimeError):
    """Adapter is missing required configuration (API key, etc.)."""


class AnthropicTarget(Target):
    id = "claude-sonnet-4-6"
    model_version = "claude-sonnet-4-6"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        cache: ResponseCache | None = None,
        budget: BudgetGuard | None = None,
        max_retries: int = 3,
    ) -> None:
        super().__init__(cache=cache, budget=budget)
        key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise ConfigError(
                "ANTHROPIC_API_KEY is not set. Add it to .env (see .env.example) "
                "or pass api_key=... to AnthropicTarget()."
            )
        self._client = AsyncAnthropic(api_key=key, max_retries=max_retries)

    async def _send_uncached(
        self,
        messages: list[Message],
        system: str | None,
        max_tokens: int,
    ) -> TargetResponse:
        # The Anthropic SDK takes `system` separately, not as a Message.
        sdk_messages: list[dict[str, Any]] = [
            {"role": m.role, "content": m.content} for m in messages if m.role != "system"
        ]

        kwargs: dict[str, Any] = {
            "model": self.model_version,
            "messages": sdk_messages,
            "max_tokens": max_tokens,
        }
        if system is not None:
            kwargs["system"] = system

        t0 = time.monotonic()
        msg = await self._client.messages.create(**kwargs)
        latency_ms = int((time.monotonic() - t0) * 1000)

        # Anthropic returns content as a list of blocks; concatenate text blocks.
        text_parts: list[str] = []
        for block in msg.content:
            if getattr(block, "type", None) == "text":
                text_parts.append(block.text)
        response_text = "".join(text_parts)

        in_tok = msg.usage.input_tokens
        out_tok = msg.usage.output_tokens
        return TargetResponse(
            target_id=self.id,
            model_version=self.model_version,
            request_messages=messages,
            response_text=response_text,
            finish_reason=msg.stop_reason,
            input_tokens=in_tok,
            output_tokens=out_tok,
            cost_usd=cost_for(self.model_version, in_tok, out_tok),
            latency_ms=latency_ms,
            attempt=1,
        )
