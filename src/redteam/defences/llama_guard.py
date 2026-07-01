"""Llama Guard 4 pre / post filter (via Ollama).

Llama Guard 4 is Meta's content classifier (April 2025). We use it as a
detector — its job is to read either the user input (pre-filter) or the
assistant output (post-filter) and answer "safe" or "unsafe".

Ollama's `llama-guard4:12b` formats the prompt automatically when called
through /api/chat with role="user", so we just send the text we want
classified. The model returns either:

    safe

or

    unsafe
    S<n>

where S<n> is the violation category. We **fail closed**: only a clean
"safe" verdict passes; anything else — "unsafe...", an empty string, or an
error/garbled response from the guard — is treated as unsafe. A content
filter that cannot get a clean read should block, not wave content through.

Lesson L10 / kit notes: ensure `ollama serve` is running before the
target is constructed. The OllamaTarget.healthcheck() should be called
once at orchestrator startup.
"""

from __future__ import annotations

from redteam.defences.base import Defence, SendLike, synthetic_refusal
from redteam.schemas import Message, TargetResponse


def _is_unsafe(verdict: str) -> bool:
    """Fail CLOSED: only a first line of exactly "safe" is treated as safe.

    An empty, error, or unrecognised verdict from the guard counts as unsafe
    so a broken guard blocks content instead of silently passing it.
    """
    first_line = (verdict.strip().splitlines() or [""])[0].strip().lower()
    return first_line != "safe"


async def _classify(guard: SendLike, text: str) -> tuple[bool, str]:
    """Send `text` to Llama Guard. Returns (is_unsafe, raw verdict)."""
    resp = await guard.send([Message(role="user", content=text)], max_tokens=64)
    return _is_unsafe(resp.response_text), resp.response_text


class LlamaGuard4PreFilter(Defence):
    """Classify input BEFORE forwarding. Refuse with a synthetic response on flag."""

    defence_id = "llamaguard4-pre"

    def __init__(self, inner: SendLike, *, guard: SendLike) -> None:
        super().__init__(inner)
        self._guard = guard

    async def send(
        self,
        messages: list[Message],
        *,
        system: str | None = None,
        max_tokens: int = 1024,
    ) -> TargetResponse:
        # Concatenate user messages for classification (multi-turn = full transcript).
        user_text = "\n\n".join(m.content for m in messages if m.role == "user")
        unsafe, verdict = await _classify(self._guard, user_text)
        if unsafe:
            return synthetic_refusal(
                target_id=self.id,
                model_version=self.model_version,
                request_messages=messages,
                reason=f"Llama Guard 4 flagged input: {verdict.strip()}",
                by="LlamaGuard4-pre",
            )
        return await self._inner.send(messages, system=system, max_tokens=max_tokens)


class LlamaGuard4PostFilter(Defence):
    """Forward to inner; if Guard flags the OUTPUT, replace with a refusal."""

    defence_id = "llamaguard4-post"

    def __init__(self, inner: SendLike, *, guard: SendLike) -> None:
        super().__init__(inner)
        self._guard = guard

    async def send(
        self,
        messages: list[Message],
        *,
        system: str | None = None,
        max_tokens: int = 1024,
    ) -> TargetResponse:
        response = await self._inner.send(messages, system=system, max_tokens=max_tokens)
        unsafe, verdict = await _classify(self._guard, response.response_text)
        if unsafe:
            # Keep the cost / latency from the underlying call so the budget
            # roll-up is honest, but rewrite the response text.
            return response.model_copy(
                update={
                    "response_text": (
                        f"[REFUSED BY LlamaGuard4-post] Output flagged by Llama Guard 4: "
                        f"{verdict.strip()}"
                    ),
                    "finish_reason": "refused_by_defence",
                }
            )
        return response
