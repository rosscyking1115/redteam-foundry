"""Fire the absence detector, so a 0.00% rate means something.

A reported absence rate of exactly 0.00% — on a metric whose whole job is to
notice that responses came back empty — is indistinguishable from a counter
that *cannot* return non-zero. That is the failure this repository has
catalogued repeatedly in
`docs/findings/what-does-this-metric-return-when-nothing-happened.md`.

These tests inject a deliberately blank response and a deliberately unparseable
one and assert the counters increment. Without them, "absence rate 0.00%" is
not evidence; with them, it is.

The reporter lives in scripts/, which is not an importable package, so it is
loaded by path.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

_SPEC = importlib.util.spec_from_file_location(
    "report_locale_provenance",
    Path(__file__).resolve().parents[2] / "scripts" / "report_locale_provenance.py",
)
assert _SPEC and _SPEC.loader
report = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = report
_SPEC.loader.exec_module(report)

CONDITIONS = report.CONDITIONS
N = len(CONDITIONS)


def _cell(raw: str, verdict: int) -> dict[str, Any]:
    return {"raw": raw, "verdict": verdict, "split": "harmful", "tai_collapse": False}


def _healthy_item() -> dict[str, Any]:
    return {c: _cell("<score>yes</score>", 1) for c in CONDITIONS}


def test_healthy_run_reports_zero_absence() -> None:
    """The baseline: a clean corpus really does score 0."""
    counts = report.absence_counts({"a": _healthy_item(), "b": _healthy_item()}, N)
    assert counts["calls"] == 2 * N
    assert counts["empty_responses"] == 0
    assert counts["unparseable_verdicts"] == 0
    assert counts["items_missing_a_cell"] == 0


def test_blank_response_increments_the_empty_counter() -> None:
    """Inject an empty response. If this does not fire, 0.00% is meaningless."""
    item = _healthy_item()
    item["glyph_only"] = _cell("", report.UNPARSEABLE)

    counts = report.absence_counts({"a": item}, N)
    assert counts["empty_responses"] == 1, "detector cannot see a blank response"


def test_whitespace_only_response_counts_as_empty() -> None:
    """A response of spaces and newlines is not a response."""
    item = _healthy_item()
    item["hong_kong"] = _cell("   \n\t ", report.UNPARSEABLE)

    counts = report.absence_counts({"a": item}, N)
    assert counts["empty_responses"] == 1


def test_unparseable_verdict_increments_its_own_counter() -> None:
    """Non-empty but unscoreable output is a distinct failure from silence."""
    item = _healthy_item()
    item["dictionary_localised"] = _cell("I cannot assess this.", report.UNPARSEABLE)

    counts = report.absence_counts({"a": item}, N)
    assert counts["unparseable_verdicts"] == 1, "detector cannot see an unparseable verdict"
    # Non-empty, so it must NOT be double-counted as silence.
    assert counts["empty_responses"] == 0


def test_missing_cell_is_counted_separately_from_a_bad_one() -> None:
    """An item the run never reached is not an item the guard failed on."""
    item = _healthy_item()
    del item["hong_kong"]

    counts = report.absence_counts({"a": item}, N)
    assert counts["items_missing_a_cell"] == 1
    assert counts["empty_responses"] == 0
    assert counts["unparseable_verdicts"] == 0


def test_unparseable_cells_are_excluded_from_paired_tests_not_scored_as_agreement() -> None:
    """The reason absence is tracked at all.

    Two conditions that both returned nothing must not register as "the guard
    agreed". They are dropped from the pair and reported as excluded.
    """
    item = _healthy_item()
    item["native"] = _cell("", report.UNPARSEABLE)
    item["glyph_only"] = _cell("", report.UNPARSEABLE)

    result = report.change_rate([item], "native", "glyph_only")
    assert result["n"] == 0, "a pair with no verdicts must contribute no comparison"
    assert result["excluded_unparseable"] == 1
    assert result["changed"] == 0
    # And the rate is 0.0 on an empty sample — which is why n must be read too.
    assert result["rate"] == 0.0
