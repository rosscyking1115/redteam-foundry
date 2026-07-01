"""OpenAI adapter — scaffolded but disabled by default.

Phase 2 ships this stub so the architecture supports a second frontier
provider without rewriting interfaces. Activated when an OPENAI_API_KEY is
present in the environment; absent that, every call raises ConfigError so
the failure is loud, not silent.

Naming note: the file is openai_target.py (not openai.py) to avoid
shadowing the official `openai` package in imports.
"""

from __future__ import annotations

import os
import time
from typing import Any

from redteam.budget import BudgetGuard
from redteam.cache import ResponseCache
from redteam.schemas import Message, TargetResponse
from redteam.targets._pricing import cost_for, has_pricing
from redteam.targets.anthropic import ConfigError
from redteam.targets.base import Target


class OpenAITarget(Target):
    id = "gpt-5"
    model_version = "gpt-5"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        cache: ResponseCache | None = None,
        budget: BudgetGuard | None = None,
    ) -> None:
        super().__init__(cache=cache, budget=budget)
        key = api_key or os.environ.get("OPENAI_API_KEY")
        if not key:
            raise ConfigError(
                "OPENAI_API_KEY is not set. The OpenAI target is opt-in for Phase 2 — "
                "set the env var to enable it, or stick to the Anthropic + Ollama targets."
            )
        # Fail loud if the model has no pricing: running it would silently
        # record $0 and bypass the budget guard entirely. Add a real entry to
        # _pricing.py before enabling this target.
        if not has_pricing(self.model_version):
            raise ConfigError(
                f"No pricing configured for OpenAI model {self.model_version!r}. Add it to "
                "src/redteam/targets/_pricing.py before enabling this target — it must not "
                "run un-metered against the budget guard."
            )
        # Lazy SDK import so users without an OpenAI key don't pay the import cost.
        from openai import AsyncOpenAI

        self._client = AsyncOpenAI(api_key=key)

    async def _send_uncached(
        self,
        messages: list[Message],
        system: str | None,
        max_tokens: int,
    ) -> TargetResponse:
        sdk_messages: list[dict[str, Any]] = []
        if system is not None:
            sdk_messages.append({"role": "system", "content": system})
        sdk_messages.extend({"role": m.role, "content": m.content} for m in messages)

        t0 = time.monotonic()
        completion = await self._client.chat.completions.create(
            model=self.model_version,
            messages=sdk_messages,  # type: ignore[arg-type]
            max_completion_tokens=max_tokens,
        )
        latency_ms = int((time.monotonic() - t0) * 1000)

        choice = completion.choices[0]
        response_text = choice.message.content or ""
        usage = completion.usage
        in_tok = usage.prompt_tokens if usage else 0
        out_tok = usage.completion_tokens if usage else 0

        # Pricing is guaranteed present (checked in __init__), so this never
        # silently zero-costs — the budget guard always sees a real number.
        cost = cost_for(self.model_version, in_tok, out_tok)

        return TargetResponse(
            target_id=self.id,
            model_version=self.model_version,
            request_messages=messages,
            response_text=response_text,
            finish_reason=choice.finish_reason,
            input_tokens=in_tok,
            output_tokens=out_tok,
            cost_usd=cost,
            latency_ms=latency_ms,
            attempt=1,
        )
