"""Schema validation tests."""

from __future__ import annotations

from decimal import Decimal

import pytest
from pydantic import ValidationError

from redteam.schemas import AttackCase, Message, ScoredCase, TargetResponse


def _ok_case() -> AttackCase:
    return AttackCase(
        id="abc123def456",
        source="advbench",
        category="harmful_content",
        severity="high",
        prompt="benign placeholder for schema test",
        expected_behaviour="refuse",
    )


def test_attack_case_minimum_fields() -> None:
    case = _ok_case()
    assert case.id == "abc123def456"
    assert case.references == []
    assert case.excluded_topics == []


def test_attack_case_is_frozen() -> None:
    case = _ok_case()
    with pytest.raises(ValidationError):
        case.prompt = "mutated"  # type: ignore[misc]


def test_attack_case_rejects_unknown_source() -> None:
    with pytest.raises(ValidationError):
        AttackCase(
            id="x",
            source="not-a-real-dataset",  # type: ignore[arg-type]
            category="harmful_content",
            severity="high",
            prompt="x",
            expected_behaviour="refuse",
        )


def test_attack_case_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        AttackCase(  # type: ignore[call-arg]
            id="x",
            source="advbench",
            category="harmful_content",
            severity="high",
            prompt="x",
            expected_behaviour="refuse",
            unexpected_extra="boom",
        )


def test_target_response_cost_is_decimal() -> None:
    resp = TargetResponse(
        target_id="claude-sonnet-4-6",
        model_version="claude-sonnet-4-6",
        request_messages=[Message(role="user", content="hi")],
        response_text="hello",
        finish_reason="end_turn",
        cost_usd=Decimal("0.0123"),
    )
    assert isinstance(resp.cost_usd, Decimal)
    assert resp.attempt == 1


def test_scored_case_label_constrained() -> None:
    resp = TargetResponse(
        target_id="t",
        model_version="v",
        request_messages=[Message(role="user", content="hi")],
        response_text="r",
    )
    sc = ScoredCase(
        attack_case_id="abc",
        target_response=resp,
        final_label="refused",
    )
    assert sc.final_label == "refused"
    with pytest.raises(ValidationError):
        ScoredCase(
            attack_case_id="abc",
            target_response=resp,
            final_label="not-a-label",  # type: ignore[arg-type]
        )
