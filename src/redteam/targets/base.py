"""Target ABC — every concrete adapter inherits from this.

The base class wires the cache + budget gates around every call so that
individual adapters only have to implement `_send_uncached`. This keeps
the safety-critical book-keeping in one place per L3 / L2 of the kit.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal

from redteam.budget import BudgetGuard, get_budget
from redteam.cache import ResponseCache
from redteam.schemas import Message, TargetResponse
from redteam.targets._pricing import estimate_cost


def estimate_input_tokens(messages: list[Message], system: str | None) -> int:
    """Cheap upper-bound estimate: ~1 token per 3 characters.

    Real tokenisers (tiktoken / Anthropic's) would be more accurate, but
    cost a dependency and runtime. Over-estimating is fine — it just makes
    the budget guard slightly more conservative.
    """
    chars = sum(len(m.content) for m in messages) + (len(system) if system else 0)
    return max(1, chars // 3)


class Target(ABC):
    """Subclass with concrete `id`, `model_version`, and `_send_uncached`."""

    id: str
    model_version: str

    def __init__(
        self,
        *,
        cache: ResponseCache | None = None,
        budget: BudgetGuard | None = None,
    ) -> None:
        # cache=None means "do not cache"; pass ResponseCache() for default disk cache.
        self.cache = cache
        self.budget = budget or get_budget()

    async def send(
        self,
        messages: list[Message],
        *,
        system: str | None = None,
        max_tokens: int = 1024,
    ) -> TargetResponse:
        """Cached, budget-gated dispatch. Use this, not _send_uncached."""
        cache_key = self._cache_key(messages, system, max_tokens)
        if self.cache is not None:
            cached = self.cache.get(target_id=self.id, key=cache_key)
            if cached is not None:
                return cached

        # Pre-call budget check using a worst-case estimate. This RESERVES the
        # estimate against the cap so concurrent calls can't collectively
        # overshoot; the reservation is unwound below on success or failure.
        estimated_input = estimate_input_tokens(messages, system)
        est = estimate_cost(self.model_version, estimated_input, max_tokens)
        self.budget.check_can_spend(est)

        # The actual API call happens here.
        try:
            response = await self._send_uncached(messages, system, max_tokens)
        except BaseException:
            self.budget.release(est)  # call never completed — free the reservation
            raise

        # Reconcile the reservation to realised spend (may raise if underran).
        self.budget.record_spend(response.cost_usd, est)

        if self.cache is not None:
            self.cache.put(target_id=self.id, key=cache_key, response=response)
        return response

    @abstractmethod
    async def _send_uncached(
        self,
        messages: list[Message],
        system: str | None,
        max_tokens: int,
    ) -> TargetResponse:
        """Concrete adapter: hit the upstream API, return TargetResponse."""

    def _cache_key(self, messages: list[Message], system: str | None, max_tokens: int) -> str:
        return ResponseCache.make_key(
            target_id=self.id,
            model_version=self.model_version,
            messages=messages,
            system=system,
            max_tokens=max_tokens,
        )

    @staticmethod
    def _zero() -> Decimal:  # convenience for adapter __init__ paths
        return Decimal("0")
