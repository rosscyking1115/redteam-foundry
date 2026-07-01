"""Pydantic v2 schemas for the red-team harness.

These are the boundary types between the major subsystems:
    corpora  -> AttackCase
    targets  -> TargetResponse
    scorers  -> ScoredCase

All schemas are `extra="forbid"` to catch typos in config / runtime payloads
early. AttackCase is `frozen=True` because cases flow through async pipelines
and we never want them mutated in place.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

Source = Literal[
    "advbench",
    "jailbreakbench",
    "harmbench",
    "agentdojo",
    # Not an adversarial corpus: a benign control set used to measure the
    # false-refusal (over-blocking) cost of a defence. Kept out of the
    # adversarial LOADERS registry so `corpora audit/list` stay adversarial-only.
    "benign_control",
    # Benign control set in non-English / code-switched languages, for
    # measuring language-specific false-refusal (Phase 4).
    "benign_multilingual",
]

Category = Literal[
    "jailbreak",
    "prompt_injection_direct",
    "prompt_injection_indirect",
    "harmful_content",
    "data_exfiltration",
    "role_play",
    # A legitimate request the model SHOULD complete; a refusal here is a
    # FALSE refusal. Used only by the benign control set.
    "benign",
]

Severity = Literal["low", "medium", "high"]

ExpectedBehaviour = Literal["refuse", "complete_safely", "flag"]

# Mirrors ETHICS.md "Excluded categories". Exhaustive — adding a new excluded
# topic here is the single source of truth that propagates to the filter and
# the audit test.
ExcludedTopic = Literal[
    "csam",
    "bio_chem_radiological_nuclear_weapons_synthesis",
    "detailed_self_harm_methods",
]

FinalLabel = Literal["blocked", "leaked", "refused", "unclear"]


# ---------------------------------------------------------------------------
# Conversation primitives
# ---------------------------------------------------------------------------


class Message(BaseModel):
    """OpenAI/Anthropic-compatible chat message."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    role: Literal["system", "user", "assistant"]
    content: str


# ---------------------------------------------------------------------------
# Pipeline records
# ---------------------------------------------------------------------------


class AttackCase(BaseModel):
    """A single adversarial prompt with provenance and expected behaviour.

    `excluded_topics` is the audit field: empty for cases that pass the
    exclusion filter, populated only on records exported by the filter as
    "this is what I dropped and why".
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    source: Source
    category: Category
    severity: Severity
    prompt: str
    expected_behaviour: ExpectedBehaviour
    references: list[str] = Field(default_factory=list)
    excluded_topics: list[ExcludedTopic] = Field(default_factory=list)
    # Optional language tag (e.g. "en", "zh-Hant", "zh-Hans", "ja", "ko",
    # "mixed-en-zh"). Set on the multilingual control set; None elsewhere.
    lang: str | None = None


class TargetResponse(BaseModel):
    """Outcome of a single Target.send() call.

    `cost_usd` is a Decimal because per-token billing arithmetic with floats
    accumulates rounding error fast across thousands of cases.
    """

    model_config = ConfigDict(extra="forbid")

    target_id: str
    model_version: str
    request_messages: list[Message]
    response_text: str
    finish_reason: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: Decimal = Decimal("0")
    latency_ms: int = 0
    attempt: int = 1


class ScoredCase(BaseModel):
    """One AttackCase x one TargetResponse, with rule + judge verdicts."""

    model_config = ConfigDict(extra="forbid")

    attack_case_id: str
    target_response: TargetResponse
    defences_applied: list[str] = Field(default_factory=list)
    rule_score: dict[str, float] = Field(default_factory=dict)
    judge_score: dict[str, float] = Field(default_factory=dict)
    final_label: FinalLabel
    notes: str | None = None
