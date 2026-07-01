"""Multilingual benign control set + per-language FRR tests (Phase 4)."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

from redteam.compare import frr_by_language
from redteam.corpora._filters import filter_prompt
from redteam.corpora.taxonomy import detect_language
from redteam.multilingual import (
    LANGUAGES,
    MULTILINGUAL_BENIGN,
    export_multilingual_jsonl,
)
from redteam.orchestrator import CaseOutcome, RunConfig, RunResult, iter_attack_cases
from redteam.schemas import AttackCase


def test_multilingual_set_well_formed() -> None:
    assert len(MULTILINGUAL_BENIGN) >= 20
    for c in MULTILINGUAL_BENIGN:
        assert c.source == "benign_multilingual"
        assert c.category == "benign"
        assert c.expected_behaviour == "complete_safely"
        assert c.lang  # every multilingual case carries a precise lang tag


def test_ids_unique() -> None:
    ids = [c.id for c in MULTILINGUAL_BENIGN]
    assert len(ids) == len(set(ids))


def test_language_coverage() -> None:
    assert {"zh-Hant", "zh-Hans", "ja", "ko"} <= set(LANGUAGES)
    assert any(lang.startswith("mixed") for lang in LANGUAGES)


def test_none_flagged_by_exclusion_filter() -> None:
    for c in MULTILINGUAL_BENIGN:
        assert not filter_prompt(c.prompt, source="advbench").excluded, c.prompt


def test_detector_agrees_with_recorded_language() -> None:
    expect = {
        "zh-Hans": "zh",
        "zh-Hant": "zh",
        "ja": "ja",
        "ko": "ko",
        "mixed-en-zh": "zh",
        "mixed-en-ja": "ja",
        "mixed-en-ko": "ko",
    }
    for c in MULTILINGUAL_BENIGN:
        tag = detect_language(c.prompt)
        assert tag.label == expect[c.lang or ""], (c.lang, tag.label, c.prompt)
        if (c.lang or "").startswith("mixed"):
            assert tag.mixed is True, c.prompt
        else:
            assert tag.mixed is False, c.prompt


def test_orchestrator_resolves_multilingual_source() -> None:
    cfg = RunConfig.model_validate(
        {
            "name": "ml",
            "target": "claude-sonnet-4-6",
            "corpora": [{"source": "benign_multilingual"}],
        }
    )
    cases = iter_attack_cases(cfg)
    assert len(cases) == len(MULTILINGUAL_BENIGN)
    assert all(c.source == "benign_multilingual" for c in cases)


def test_export_roundtrips(tmp_path: Path) -> None:
    out = export_multilingual_jsonl(tmp_path / "ml.jsonl")
    lines = out.read_text(encoding="utf-8").splitlines()
    assert len(lines) == len(MULTILINGUAL_BENIGN)
    first = AttackCase.model_validate(json.loads(lines[0]))
    assert first.lang


# ---------------------------------------------------------------------------
# Per-language FRR
# ---------------------------------------------------------------------------


def _outcome(case: AttackCase, *, refused: bool) -> CaseOutcome:
    return CaseOutcome(
        case_id=case.id,
        case_source=case.source,
        case_category=case.category,
        case_severity=case.severity,
        prompt=case.prompt,
        response_text="...",
        finish_reason="stop",
        is_refusal=refused,
        matched_phrase="I cannot" if refused else None,
        cost_usd=Decimal("0"),
        input_tokens=1,
        output_tokens=1,
        latency_ms=1,
    )


def _run_over(outcomes: list[CaseOutcome]) -> RunResult:
    n = len(outcomes)
    refusals = sum(1 for o in outcomes if o.is_refusal)
    return RunResult(
        run_name="ml",
        target="claude-sonnet-4-6",
        defences=[],
        cases_total=n,
        refusals=refusals,
        asr=0.0,
        refusal_rate=refusals / n if n else 0.0,
        total_cost_usd=Decimal("0"),
        started_at="2026-07-01T00:00:00+00:00",
        finished_at="2026-07-01T00:00:01+00:00",
        outcomes=outcomes,
    )


def test_frr_by_language_uses_recorded_lang_to_split_hant_hans() -> None:
    hant = next(c for c in MULTILINGUAL_BENIGN if c.lang == "zh-Hant")
    hans = next(c for c in MULTILINGUAL_BENIGN if c.lang == "zh-Hans")
    run = _run_over([_outcome(hant, refused=True), _outcome(hans, refused=False)])

    report = frr_by_language(run, MULTILINGUAL_BENIGN)
    by_lang = {r.lang: r for r in report.rows}
    # Recorded lang keeps Traditional and Simplified separate.
    assert by_lang["zh-Hant"].frr == 1.0
    assert by_lang["zh-Hans"].frr == 0.0
    assert report.overall_frr == 0.5


def test_frr_by_language_falls_back_to_detection_without_cases() -> None:
    hant = next(c for c in MULTILINGUAL_BENIGN if c.lang == "zh-Hant")
    hans = next(c for c in MULTILINGUAL_BENIGN if c.lang == "zh-Hans")
    run = _run_over([_outcome(hant, refused=True), _outcome(hans, refused=False)])

    # No cases -> script detection collapses both to "zh".
    report = frr_by_language(run)
    by_lang = {r.lang: r for r in report.rows}
    assert set(by_lang) == {"zh"}
    assert by_lang["zh"].n == 2
    assert by_lang["zh"].frr == 0.5
