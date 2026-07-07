"""Per-model token pricing in USD. Verified 2026-05-08.

Re-verify when bumping a model pin. Keep the keys aligned with the dated
model IDs we use in the targets and judges.

Sources:
- https://platform.claude.com/docs/en/about-claude/pricing
"""

from __future__ import annotations

from decimal import Decimal


class PricingMissing(KeyError):
    """Raised when no pricing entry exists for a given model_version."""


# Per-million-token prices in USD.
PRICING_PER_MTOK: dict[str, dict[str, Decimal]] = {
    # Anthropic
    "claude-sonnet-4-6": {"input": Decimal("3.00"), "output": Decimal("15.00")},
    "claude-haiku-4-5-20251001": {"input": Decimal("1.00"), "output": Decimal("5.00")},
    # Local models — no per-token cost. Tracked at zero so the same
    # cost-roll-up code path works.
    "llama3.1:8b": {"input": Decimal("0"), "output": Decimal("0")},
    "llama-guard4:12b": {"input": Decimal("0"), "output": Decimal("0")},
    # Positive-control target: an older, explicitly unaligned local model.
    "llama2-uncensored:7b": {"input": Decimal("0"), "output": Decimal("0")},
    # Stretch (Phase 5+)
    "facebook/Meta-SecAlign-8B": {"input": Decimal("0"), "output": Decimal("0")},
}

_MILLION = Decimal("1000000")


def has_pricing(model_version: str) -> bool:
    """True if a pricing entry exists for the model. Adapters use this to
    fail loud at construction rather than run un-metered against the budget."""
    return model_version in PRICING_PER_MTOK


def cost_for(model_version: str, input_tokens: int, output_tokens: int) -> Decimal:
    """Compute USD cost for a single call. Raises PricingMissing if unknown."""
    table = PRICING_PER_MTOK.get(model_version)
    if table is None:
        raise PricingMissing(
            f"No pricing for {model_version!r}. Add it to "
            "src/redteam/targets/_pricing.py before calling this model."
        )
    return (
        table["input"] * Decimal(input_tokens) + table["output"] * Decimal(output_tokens)
    ) / _MILLION


def estimate_cost(model_version: str, input_tokens: int, max_output_tokens: int) -> Decimal:
    """Worst-case cost estimate: assume the model emits max_output_tokens.

    Used by Target.send() for the pre-call budget check (Lesson L3 — the
    estimate trips the budget cap before we hit the API)."""
    return cost_for(model_version, input_tokens, max_output_tokens)
