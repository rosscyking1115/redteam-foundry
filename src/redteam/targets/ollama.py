"""Ollama adapter — local Llama 3.1 8B (and friends).

Talks to Ollama's HTTP API at OLLAMA_HOST (default http://localhost:11434).
Uses httpx + tenacity for connection retry — Ollama itself is fast once
warm, but the first request after model load can take 5-30s.

Lesson L10: Ollama is finicky. If `ollama serve` isn't running, every call
fails with no clear error. The constructor pings /api/tags as a healthcheck
so the failure mode is loud and early.
"""

from __future__ import annotations

import os
import time
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from redteam.budget import BudgetGuard
from redteam.cache import ResponseCache
from redteam.schemas import Message, TargetResponse
from redteam.targets._pricing import cost_for
from redteam.targets.base import Target

DEFAULT_HOST = "http://localhost:11434"


class OllamaUnavailable(RuntimeError):
    """Ollama daemon is not reachable. Run `ollama serve` (Windows: launches with the app)."""


class OllamaTarget(Target):
    """Wraps any Ollama model. Default `id` and `model_version` are llama3.1:8b."""

    id = "llama3.1-8b-local"
    model_version = "llama3.1:8b"
    # Optional Ollama context-window override (num_ctx). None => let Ollama use
    # the model default. A smaller window shrinks the KV-cache allocation, which
    # is what lets a 7B model load on a tight (8 GB) VRAM budget.
    num_ctx: int | None = None

    def __init__(
        self,
        *,
        model: str | None = None,
        host: str | None = None,
        cache: ResponseCache | None = None,
        budget: BudgetGuard | None = None,
        timeout: float = 120.0,
        num_ctx: int | None = None,
    ) -> None:
        super().__init__(cache=cache, budget=budget)
        if model is not None:
            self.model_version = model
        if num_ctx is not None:
            self.num_ctx = num_ctx
        self.host = (host or os.environ.get("OLLAMA_HOST") or DEFAULT_HOST).rstrip("/")
        self._timeout = timeout

    async def healthcheck(self) -> None:
        """Raise OllamaUnavailable if the daemon isn't responding."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.host}/api/tags")
                resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise OllamaUnavailable(
                f"Cannot reach Ollama at {self.host}. Is `ollama serve` running? "
                "On Windows the daemon starts with the Ollama app — open it from the Start menu."
            ) from exc

    @retry(
        retry=retry_if_exception_type(httpx.ConnectError),
        stop=stop_after_attempt(3),
        wait=wait_exponential_jitter(initial=1.0, max=8.0),
        reraise=True,
    )
    async def _send_uncached(
        self,
        messages: list[Message],
        system: str | None,
        max_tokens: int,
    ) -> TargetResponse:
        chat_messages: list[dict[str, Any]] = []
        if system is not None:
            chat_messages.append({"role": "system", "content": system})
        chat_messages.extend({"role": m.role, "content": m.content} for m in messages)

        options: dict[str, Any] = {"num_predict": max_tokens}
        if self.num_ctx is not None:
            options["num_ctx"] = self.num_ctx
        payload = {
            "model": self.model_version,
            "messages": chat_messages,
            "stream": False,
            "options": options,
        }

        t0 = time.monotonic()
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(f"{self.host}/api/chat", json=payload)
            resp.raise_for_status()
            body = resp.json()
        latency_ms = int((time.monotonic() - t0) * 1000)

        # Ollama's /api/chat returns: {"message": {"role": "...", "content": "..."},
        #                              "prompt_eval_count": N, "eval_count": M, ... }
        message = body.get("message") or {}
        response_text = message.get("content", "")
        in_tok = int(body.get("prompt_eval_count", 0))
        out_tok = int(body.get("eval_count", 0))
        finish_reason = "stop" if body.get("done") else None

        return TargetResponse(
            target_id=self.id,
            model_version=self.model_version,
            request_messages=messages,
            response_text=response_text,
            finish_reason=finish_reason,
            input_tokens=in_tok,
            output_tokens=out_tok,
            cost_usd=cost_for(self.model_version, in_tok, out_tok),
            latency_ms=latency_ms,
            attempt=1,
        )


class Llama2UncensoredTarget(OllamaTarget):
    """Positive-control target — an older, explicitly *unaligned* local model.

    This is not a real deployment target: it exists so the harness can be shown
    to report a *high* attack-success rate when the model under test is actually
    vulnerable. Running the known-vulnerable config through the identical
    run/score/cross-judge pipeline that scores ~0% on frontier models is the
    control that rules out "the 0% is the harness under-eliciting" (METHODOLOGY
    §12.5). Distinct `id`/`model_version` give it its own cache namespace.
    """

    id = "llama2-uncensored-local"
    model_version = "llama2-uncensored:7b"
    # 1024-token window: comfortably covers a (short) AdvBench prompt plus the
    # 256-token completion, while keeping the KV cache / prompt-cache footprint
    # small enough to load and stay resident on an 8 GB-VRAM machine.
    num_ctx = 1024
