"""Scorer registry.

Phase 3 ships only the rule-based refusal-keyword scorer. The LLM-judge
scorer + 5% human spot-check land in Phase 4.
"""

from __future__ import annotations

from redteam.scorers.refusal_keywords import RefusalScore, score_refusal

__all__ = ["RefusalScore", "score_refusal"]
