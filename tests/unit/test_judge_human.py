"""Human spot-check + Cohen's kappa tests.

Defends: the human spot-check export and the Cohen's-kappa helper used as a tertiary validation check.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from redteam.scorers.judge_human import (
    _binary_kappa,
    _is_sampled,
    compute_kappa,
    export_for_human_review,
)


def _write_run(path: Path, n_cases: int = 100) -> None:
    """Write a synthetic run JSON with `n_cases` outcomes."""
    payload = {
        "run_name": "fixture",
        "target": "claude-sonnet-4-6",
        "defences": [],
        "cases_total": n_cases,
        "refusals": 0,
        "asr": 0.0,
        "refusal_rate": 0.0,
        "total_cost_usd": "0",
        "started_at": "2026-05-09T00:00:00+00:00",
        "finished_at": "2026-05-09T00:00:01+00:00",
        "outcomes": [
            {
                "case_id": f"case-{i:04d}",
                "case_source": "advbench",
                "case_category": "harmful_content",
                "case_severity": "high",
                "prompt": f"prompt {i}",
                "response_text": f"response {i}" * 10,
                "finish_reason": "stop",
                "is_refusal": True,
                "matched_phrase": "I",
                "cost_usd": "0",
                "input_tokens": 1,
                "output_tokens": 1,
                "latency_ms": 1,
                "judge_asr": i % 2,
                "judge_refusal": (i + 1) % 2,
                "judge_confidence": 0.9,
                "judge_reasoning": "test",
            }
            for i in range(n_cases)
        ],
    }
    path.write_text(json.dumps(payload))


def test_sampling_deterministic_for_same_id() -> None:
    a = _is_sampled("case-0001", 0.5)
    b = _is_sampled("case-0001", 0.5)
    assert a == b


def test_sampling_pct_zero_excludes_all() -> None:
    assert not any(_is_sampled(f"case-{i}", 0.0) for i in range(100))


def test_export_writes_roughly_sample_pct(tmp_path: Path) -> None:
    run = tmp_path / "run.json"
    _write_run(run, n_cases=200)
    out = export_for_human_review(run, sample_pct=0.05)
    with out.open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    # Roughly 5% of 200 = 10. Allow slack for hash-based sampler variance.
    assert 3 <= len(rows) <= 25, f"sample size out of expected band: {len(rows)}"


def test_export_is_deterministic(tmp_path: Path) -> None:
    run = tmp_path / "run.json"
    _write_run(run, n_cases=200)
    out_a = export_for_human_review(run, sample_pct=0.05, output_csv=tmp_path / "a.csv")
    out_b = export_for_human_review(run, sample_pct=0.05, output_csv=tmp_path / "b.csv")
    assert out_a.read_text() == out_b.read_text()


def test_export_human_columns_blank(tmp_path: Path) -> None:
    run = tmp_path / "run.json"
    _write_run(run, n_cases=200)
    out = export_for_human_review(run, sample_pct=0.05)
    with out.open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        assert r["human_asr"] == ""
        assert r["human_refusal"] == ""
        assert r["notes"] == ""
        assert r["judge_asr"] in {"0", "1"}


def test_kappa_perfect_agreement_returns_one() -> None:
    score = _binary_kappa([0, 0, 1, 1, 1, 0], [0, 0, 1, 1, 1, 0])
    assert score.kappa == pytest.approx(1.0)
    assert score.agreement == 1.0


def test_kappa_perfect_disagreement_is_negative() -> None:
    score = _binary_kappa([0, 0, 1, 1], [1, 1, 0, 0])
    assert score.kappa < 0
    assert score.agreement == 0.0


def test_kappa_chance_agreement_near_zero() -> None:
    # Equal class distributions, half the labels match -> kappa ~ 0
    judge = [0, 0, 1, 1, 0, 1, 0, 1]
    human = [0, 1, 1, 0, 1, 0, 1, 1]
    score = _binary_kappa(judge, human)
    assert -0.5 <= score.kappa <= 0.5


def test_kappa_constant_raters_handled() -> None:
    # Both raters always say 0 -> no observed disagreement, no chance disagreement
    score = _binary_kappa([0, 0, 0, 0], [0, 0, 0, 0])
    assert score.kappa == 1.0


def test_compute_kappa_skips_unfilled_rows(tmp_path: Path) -> None:
    csv_path = tmp_path / "review.csv"
    with csv_path.open("w", newline="") as fh:
        w = csv.DictWriter(
            fh,
            fieldnames=[
                "judge_asr",
                "judge_refusal",
                "human_asr",
                "human_refusal",
            ],
        )
        w.writeheader()
        # 4 rows, only 2 filled by human
        w.writerow({"judge_asr": 0, "judge_refusal": 1, "human_asr": "0", "human_refusal": "1"})
        w.writerow({"judge_asr": 1, "judge_refusal": 0, "human_asr": "", "human_refusal": ""})
        w.writerow({"judge_asr": 1, "judge_refusal": 0, "human_asr": "1", "human_refusal": "0"})
        w.writerow({"judge_asr": 0, "judge_refusal": 1, "human_asr": "  ", "human_refusal": "1"})
    report = compute_kappa(csv_path)
    assert report.n_rows == 4
    assert report.n_human_filled == 2  # only rows 1 and 3 had both columns filled
    assert report.asr.kappa == pytest.approx(1.0)
