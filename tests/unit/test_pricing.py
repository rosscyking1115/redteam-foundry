"""Token-pricing tests."""

from __future__ import annotations

from decimal import Decimal

import pytest

from redteam.targets._pricing import PricingMissing, cost_for, estimate_cost


def test_sonnet_4_6_pricing_3_15() -> None:
    # $3 input + $15 output per 1M tokens. 1k in + 1k out:
    # = (3 * 1000 + 15 * 1000) / 1_000_000 = 0.018
    assert cost_for("claude-sonnet-4-6", 1000, 1000) == Decimal("0.018")


def test_haiku_4_5_pricing_1_5() -> None:
    # $1 input + $5 output per 1M tokens. 1k in + 1k out:
    # = (1 * 1000 + 5 * 1000) / 1_000_000 = 0.006
    assert cost_for("claude-haiku-4-5-20251001", 1000, 1000) == Decimal("0.006")


def test_local_models_are_free() -> None:
    assert cost_for("llama3.1:8b", 100_000, 100_000) == Decimal("0")


def test_estimate_assumes_max_output() -> None:
    # estimate uses max_output_tokens as the output count; for sonnet at 1k input
    # and 4k max output: (3 * 1000 + 15 * 4000) / 1_000_000 = 0.063
    assert estimate_cost("claude-sonnet-4-6", 1000, 4000) == Decimal("0.063")


def test_unknown_model_raises_loudly() -> None:
    with pytest.raises(PricingMissing, match="No pricing"):
        cost_for("ghost-model-9000", 100, 100)
