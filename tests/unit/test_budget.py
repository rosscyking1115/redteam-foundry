"""Budget guard unit tests."""

from __future__ import annotations

from decimal import Decimal

import pytest

from redteam.budget import BudgetExceeded, BudgetGuard, get_budget, reset_budget


def test_default_caps_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("REDTEAM_MAX_USD_PER_RUN", "10.00")
    monkeypatch.setenv("REDTEAM_MAX_USD_PER_CALL", "1.00")
    g = BudgetGuard()
    assert g.max_per_run == Decimal("10.00")
    assert g.max_per_call == Decimal("1.00")


def test_pre_call_cap_blocks_oversized_call() -> None:
    g = BudgetGuard(max_per_run_usd=Decimal("5.00"), max_per_call_usd=Decimal("0.50"))
    with pytest.raises(BudgetExceeded, match="Per-call estimate"):
        g.check_can_spend(Decimal("0.60"))


def test_pre_call_cap_blocks_total_overshoot() -> None:
    g = BudgetGuard(max_per_run_usd=Decimal("1.00"), max_per_call_usd=Decimal("1.00"))
    g.record_spend(Decimal("0.80"))
    with pytest.raises(BudgetExceeded, match="Projected run total"):
        g.check_can_spend(Decimal("0.30"))


def test_record_spend_catches_estimate_underrun() -> None:
    g = BudgetGuard(max_per_run_usd=Decimal("1.00"), max_per_call_usd=Decimal("1.00"))
    g.check_can_spend(Decimal("0.30"))  # passes
    with pytest.raises(BudgetExceeded, match="Run total"):
        g.record_spend(Decimal("1.20"))  # actual cost was much higher than estimate


def test_remaining_usd_decrements() -> None:
    g = BudgetGuard(max_per_run_usd=Decimal("5.00"), max_per_call_usd=Decimal("1.00"))
    assert g.remaining_usd == Decimal("5.00")
    g.record_spend(Decimal("0.25"))
    assert g.remaining_usd == Decimal("4.75")


def test_singleton_returns_same_instance() -> None:
    reset_budget()
    a = get_budget()
    b = get_budget()
    assert a is b


def test_reset_budget_replaces_singleton() -> None:
    a = reset_budget(max_per_run_usd=Decimal("3.00"))
    b = reset_budget(max_per_run_usd=Decimal("4.00"))
    assert a is not b
    assert b.max_per_run == Decimal("4.00")
