"""Per-run + per-call budget guard.

Lesson L3 from PROJECT-1-KIT.md: cost guards must be enforced at the
*call site*, not just in the orchestrator. A hung loop that bypasses the
orchestrator's cap can otherwise overspend.

This module exposes a process-wide singleton accessed via `get_budget()`.
Concrete Target adapters call `check_can_spend()` *before* hitting the API
and `record_spend()` *after* the response arrives. If either trips the
hard cap, `BudgetExceeded` is raised and the call aborts.

Caps are read from environment variables on first access:
    REDTEAM_MAX_USD_PER_RUN  (default: 5.00)
    REDTEAM_MAX_USD_PER_CALL (default: 0.50)

Tests should call `reset_budget()` between runs to keep state clean.
"""

from __future__ import annotations

import os
import threading
from decimal import Decimal


class BudgetExceeded(RuntimeError):
    """Raised when a Target call would exceed a configured budget cap."""


def _env_decimal(name: str, default: str) -> Decimal:
    raw = os.environ.get(name, default)
    try:
        return Decimal(raw)
    except (ArithmeticError, ValueError) as exc:
        raise ValueError(f"{name}={raw!r} is not a valid decimal") from exc


class BudgetGuard:
    """Tracks cumulative spend and enforces a per-run + per-call cap.

    Thread-safe (the eval orchestrator uses asyncio, but the underlying
    httpx clients spin worker threads on some platforms).
    """

    def __init__(
        self,
        max_per_run_usd: Decimal | None = None,
        max_per_call_usd: Decimal | None = None,
    ) -> None:
        self.max_per_run = (
            max_per_run_usd
            if max_per_run_usd is not None
            else _env_decimal("REDTEAM_MAX_USD_PER_RUN", "5.00")
        )
        self.max_per_call = (
            max_per_call_usd
            if max_per_call_usd is not None
            else _env_decimal("REDTEAM_MAX_USD_PER_CALL", "0.50")
        )
        self._spent = Decimal("0")
        self._lock = threading.Lock()

    @property
    def spent_usd(self) -> Decimal:
        return self._spent

    @property
    def remaining_usd(self) -> Decimal:
        return self.max_per_run - self._spent

    def check_can_spend(self, estimate_usd: Decimal) -> None:
        """Raise BudgetExceeded if `estimate_usd` would breach a cap."""
        if estimate_usd > self.max_per_call:
            raise BudgetExceeded(
                f"Per-call estimate ${estimate_usd} exceeds cap ${self.max_per_call} "
                f"(REDTEAM_MAX_USD_PER_CALL). Lower max_tokens or split the request."
            )
        with self._lock:
            projected = self._spent + estimate_usd
            if projected > self.max_per_run:
                raise BudgetExceeded(
                    f"Projected run total ${projected} would exceed cap ${self.max_per_run} "
                    f"(REDTEAM_MAX_USD_PER_RUN). Already spent ${self._spent}; "
                    f"remaining ${self.remaining_usd}."
                )

    def record_spend(self, actual_usd: Decimal) -> None:
        """Add an actual cost to the running total. Raises if the realised
        total breached the per-run cap (catches estimate underruns)."""
        with self._lock:
            self._spent += actual_usd
            if self._spent > self.max_per_run:
                raise BudgetExceeded(
                    f"Run total ${self._spent} exceeded cap ${self.max_per_run} "
                    f"(REDTEAM_MAX_USD_PER_RUN) on actual cost ${actual_usd}. "
                    "Pre-call estimate was too low."
                )


_singleton: BudgetGuard | None = None
_singleton_lock = threading.Lock()


def get_budget() -> BudgetGuard:
    """Return the process-wide budget guard, creating it on first access."""
    global _singleton
    if _singleton is None:
        with _singleton_lock:
            if _singleton is None:
                _singleton = BudgetGuard()
    return _singleton


def reset_budget(
    max_per_run_usd: Decimal | None = None,
    max_per_call_usd: Decimal | None = None,
) -> BudgetGuard:
    """Replace the singleton with a fresh BudgetGuard. Test-only."""
    global _singleton
    with _singleton_lock:
        _singleton = BudgetGuard(max_per_run_usd, max_per_call_usd)
    return _singleton
