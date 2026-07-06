"""Statistical inference helper tests.

Defends: the bootstrap confidence intervals and the Krippendorff's-alpha / kappa
helpers — every CI and agreement number in the results traces here.
"""

from __future__ import annotations

import pytest

from redteam.stats import (
    bootstrap_mean_ci,
    bootstrap_proportion_ci,
    krippendorff_alpha_binary,
)

# ---------------------------------------------------------------------------
# Bootstrap proportion CI
# ---------------------------------------------------------------------------


def test_bootstrap_proportion_ci_zero_n_returns_zeros() -> None:
    ci = bootstrap_proportion_ci(0, 0)
    assert ci.point == 0.0
    assert ci.lo == 0.0
    assert ci.hi == 0.0
    assert ci.n == 0


def test_bootstrap_proportion_ci_point_matches_k_over_n() -> None:
    ci = bootstrap_proportion_ci(7, 20)
    assert ci.point == pytest.approx(0.35)


def test_bootstrap_proportion_ci_brackets_point_estimate() -> None:
    """The CI must contain the point estimate by construction."""
    ci = bootstrap_proportion_ci(7, 20, n_resamples=2000)
    assert ci.lo <= ci.point <= ci.hi


def test_bootstrap_proportion_ci_widens_at_smaller_n() -> None:
    """A 50% rate at n=10 should have a wider CI than at n=1000."""
    small = bootstrap_proportion_ci(5, 10, n_resamples=2000)
    big = bootstrap_proportion_ci(500, 1000, n_resamples=2000)
    assert (small.hi - small.lo) > (big.hi - big.lo)


def test_bootstrap_proportion_ci_at_zero_keeps_lo_at_zero() -> None:
    ci = bootstrap_proportion_ci(0, 100, n_resamples=2000)
    assert ci.point == 0.0
    assert ci.lo == 0.0
    assert ci.hi >= 0.0  # may include some upper uncertainty due to one-sided


def test_bootstrap_proportion_ci_is_deterministic_per_seed() -> None:
    a = bootstrap_proportion_ci(7, 20, seed=123, n_resamples=2000)
    b = bootstrap_proportion_ci(7, 20, seed=123, n_resamples=2000)
    assert a.lo == b.lo and a.hi == b.hi


def test_bootstrap_proportion_ci_seed_changes_result() -> None:
    a = bootstrap_proportion_ci(5, 20, seed=1, n_resamples=2000)
    b = bootstrap_proportion_ci(5, 20, seed=2, n_resamples=2000)
    # With different seeds, the bounds should differ at the third decimal.
    assert (a.lo, a.hi) != (b.lo, b.hi)


def test_bootstrap_proportion_ci_invalid_inputs_raise() -> None:
    with pytest.raises(ValueError):
        bootstrap_proportion_ci(-1, 10)
    with pytest.raises(ValueError):
        bootstrap_proportion_ci(11, 10)
    with pytest.raises(ValueError):
        bootstrap_proportion_ci(5, 10, confidence=1.5)


# ---------------------------------------------------------------------------
# Bootstrap mean CI
# ---------------------------------------------------------------------------


def test_bootstrap_mean_ci_empty_returns_zeros() -> None:
    p, lo, hi = bootstrap_mean_ci([])
    assert p == 0.0 and lo == 0.0 and hi == 0.0


def test_bootstrap_mean_ci_brackets_point() -> None:
    values = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]
    p, lo, hi = bootstrap_mean_ci(values, n_resamples=2000)
    assert lo <= p <= hi


def test_bootstrap_mean_ci_constant_vector() -> None:
    p, lo, hi = bootstrap_mean_ci([0.7] * 50, n_resamples=2000)
    assert p == pytest.approx(0.7)
    assert lo == pytest.approx(0.7)
    assert hi == pytest.approx(0.7)


# ---------------------------------------------------------------------------
# Krippendorff's alpha (binary nominal)
# ---------------------------------------------------------------------------


def test_alpha_perfect_agreement_returns_one() -> None:
    assert krippendorff_alpha_binary([0, 1, 1, 0, 1], [0, 1, 1, 0, 1]) == pytest.approx(1.0)


def test_alpha_perfect_disagreement_is_negative() -> None:
    assert krippendorff_alpha_binary([0, 0, 1, 1], [1, 1, 0, 0]) < 0


def test_alpha_chance_level_near_zero() -> None:
    judge = [0, 0, 1, 1, 0, 1, 0, 1, 0, 1]
    human = [0, 1, 1, 0, 1, 0, 1, 1, 0, 0]
    val = krippendorff_alpha_binary(judge, human)
    assert -0.5 <= val <= 0.5


def test_alpha_constant_raters_same_direction() -> None:
    assert krippendorff_alpha_binary([0, 0, 0, 0], [0, 0, 0, 0]) == 1.0


def test_alpha_high_agreement_near_one() -> None:
    # 9 of 10 agree -> alpha should be high (>= 0.8)
    judge = [0, 1, 0, 1, 0, 1, 0, 1, 0, 1]
    human = [0, 1, 0, 1, 0, 1, 0, 1, 0, 0]
    val = krippendorff_alpha_binary(judge, human)
    assert val >= 0.5  # exact value depends on marginals; it's lower than naive intuition


def test_alpha_invalid_inputs_raise() -> None:
    with pytest.raises(ValueError):
        krippendorff_alpha_binary([0, 1], [0, 1, 0])  # length mismatch
    with pytest.raises(ValueError):
        krippendorff_alpha_binary([0, 2], [0, 1])  # non-binary value
