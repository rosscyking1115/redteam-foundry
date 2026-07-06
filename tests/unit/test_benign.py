"""Benign control set tests (Phase 3).

Defends: the benign control set is well-formed and labelled, so the false-refusal-rate and safe-usefulness numbers computed over it are meaningful.
"""

from __future__ import annotations

import json
from pathlib import Path

from redteam.benign import BENIGN_CONTROL, export_benign_jsonl
from redteam.corpora._filters import filter_prompt
from redteam.orchestrator import RunConfig, iter_attack_cases
from redteam.schemas import AttackCase


def test_benign_set_is_nonempty_and_well_formed() -> None:
    assert len(BENIGN_CONTROL) >= 40
    for c in BENIGN_CONTROL:
        assert c.source == "benign_control"
        assert c.category == "benign"
        assert c.expected_behaviour == "complete_safely"
        assert c.prompt.strip()


def test_benign_ids_are_unique() -> None:
    ids = [c.id for c in BENIGN_CONTROL]
    assert len(ids) == len(set(ids))


def test_benign_prompts_are_not_flagged_by_exclusion_filter() -> None:
    """Integrity: the control set must be genuinely benign — nothing in it may
    trip the CSAM / WMD / self-harm exclusion filter."""
    for c in BENIGN_CONTROL:
        result = filter_prompt(c.prompt, source="advbench")
        assert not result.excluded, (
            f"benign prompt wrongly flagged: {c.prompt!r} -> {result.topics}"
        )


def test_export_jsonl_roundtrips(tmp_path: Path) -> None:
    out = export_benign_jsonl(tmp_path / "benign.jsonl")
    lines = out.read_text(encoding="utf-8").splitlines()
    assert len(lines) == len(BENIGN_CONTROL)
    first = AttackCase.model_validate(json.loads(lines[0]))
    assert first.source == "benign_control"


def test_orchestrator_resolves_benign_source() -> None:
    cfg = RunConfig.model_validate(
        {
            "name": "frr",
            "target": "claude-sonnet-4-6",
            "corpora": [{"source": "benign_control"}],
        }
    )
    cases = iter_attack_cases(cfg)
    assert len(cases) == len(BENIGN_CONTROL)
    assert all(c.source == "benign_control" for c in cases)


def test_orchestrator_respects_benign_limit() -> None:
    cfg = RunConfig.model_validate(
        {
            "name": "frr",
            "target": "claude-sonnet-4-6",
            "corpora": [{"source": "benign_control", "limit": 5}],
        }
    )
    assert len(iter_attack_cases(cfg)) == 5
