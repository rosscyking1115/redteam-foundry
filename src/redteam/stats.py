"""Statistical inference helpers for ASR / refusal-rate metrics.

ST2.1 — addresses two limitations of the Phase 3/4 scoring pipeline:

  1. Naive proportions like "ASR = 5%" carry no usable confidence interval
     at the small sample sizes (n=20-100) typical of a defence eval. The
     2026 paper "Don't Use the CLT in LLM Evals With Fewer Than a Few
     Hundred" (Madaan et al.) shows that CLT-based intervals on judge
     scores have near-zero coverage in practice. We use percentile
     bootstrap instead — wider intervals, but actually defensible at
     small n.

  2. Cohen's kappa requires exactly two raters and breaks down on
     highly-skewed marginals (the "kappa paradox"). Krippendorff's alpha
     is the field-standard alternative for inter-rater reliability when
     you want a single number that generalises. Anthropic Fellows /
     AISI work cite Krippendorff's alpha near 0.8 as the bar for a
     reliable judge.

Pure stdlib — no numpy / scipy dependency. Bootstrap is deterministic
via a seeded RNG so report numbers are reproducible across runs.
"""

from __future__ import annotations

import math
import random
from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict, Field

# Default RNG seed for bootstrap. Override per-call with `seed=` if you
# want to characterise sampling variability across seeds — but the default
# keeps published numbers reproducible.
_DEFAULT_SEED = 42


class ProportionCI(BaseModel):
    """Bootstrap confidence interval on a binary proportion (e.g., ASR)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    point: float = Field(ge=0.0, le=1.0, description="Sample proportion (k/n).")
    lo: float = Field(ge=0.0, le=1.0)
    hi: float = Field(ge=0.0, le=1.0)
    n: int = Field(ge=0)
    confidence: float = Field(ge=0.0, le=1.0)
    n_resamples: int = Field(ge=1)


def bootstrap_proportion_ci(
    successes: int,
    n: int,
    *,
    confidence: float = 0.95,
    n_resamples: int = 10_000,
    seed: int = _DEFAULT_SEED,
) -> ProportionCI:
    """Percentile-bootstrap CI on a binary proportion.

    `successes` and `n` describe the original observation; we resample
    n binary draws (with replacement) from the implicit 0/1 vector and
    take the central `confidence` interval of the resampled means.

    For binary data this is equivalent to a parametric bootstrap on
    Bernoulli(p) — but the implementation below works on the actual
    observed vector, which is what the literature recommends for
    consistency with multi-class metrics.
    """
    if n <= 0:
        return ProportionCI(
            point=0.0, lo=0.0, hi=0.0, n=0, confidence=confidence, n_resamples=n_resamples
        )
    if not (0.0 < confidence < 1.0):
        raise ValueError(f"confidence must be in (0,1); got {confidence}")
    if successes < 0 or successes > n:
        raise ValueError(f"successes={successes} not in [0, {n}]")

    rng = random.Random(seed)
    # Implicit 0/1 vector: `successes` ones followed by `n - successes` zeros
    # We don't materialise it; sampling is a binomial with p = successes/n.
    p = successes / n
    means = [rng.binomialvariate(n, p) / n for _ in range(n_resamples)]
    means.sort()

    alpha = 1.0 - confidence
    lo_idx = max(0, math.floor((alpha / 2) * n_resamples))
    hi_idx = min(n_resamples - 1, math.ceil((1 - alpha / 2) * n_resamples) - 1)
    return ProportionCI(
        point=p,
        lo=means[lo_idx],
        hi=means[hi_idx],
        n=n,
        confidence=confidence,
        n_resamples=n_resamples,
    )


def bootstrap_mean_ci(
    values: Sequence[float],
    *,
    confidence: float = 0.95,
    n_resamples: int = 10_000,
    seed: int = _DEFAULT_SEED,
) -> tuple[float, float, float]:
    """Percentile-bootstrap CI on the mean of an arbitrary numeric vector.

    Returns (point, lo, hi). For non-binary metrics — e.g., judge
    confidence, latency, cost per case.
    """
    if not values:
        return 0.0, 0.0, 0.0
    if not (0.0 < confidence < 1.0):
        raise ValueError(f"confidence must be in (0,1); got {confidence}")

    rng = random.Random(seed)
    n = len(values)
    point = sum(values) / n
    means = []
    for _ in range(n_resamples):
        # `random.choices` samples with replacement (which is what bootstrap
        # needs). Faster than a Python loop for large n_resamples.
        sample = rng.choices(values, k=n)
        means.append(sum(sample) / n)
    means.sort()

    alpha = 1.0 - confidence
    lo_idx = max(0, math.floor((alpha / 2) * n_resamples))
    hi_idx = min(n_resamples - 1, math.ceil((1 - alpha / 2) * n_resamples) - 1)
    return point, means[lo_idx], means[hi_idx]


# ---------------------------------------------------------------------------
# Krippendorff's alpha — binary nominal, two raters, no missing data
# ---------------------------------------------------------------------------


def krippendorff_alpha_binary(rater_a: Sequence[int], rater_b: Sequence[int]) -> float:
    """Krippendorff's alpha for binary nominal data, two raters, no missing
    values. For this restricted case the formula reduces to:

        alpha = 1 - Do / De

    where Do is the observed disagreement and De is the disagreement
    expected under random chance (computed from the marginal distribution
    pooled across both raters).

    Returns 1.0 for perfect agreement, 0.0 for chance-level, negative for
    systematic disagreement. NaN-safe via convention: when De==0 (both
    raters constant in the same direction) we return 1.0 if Do==0 else 0.0.

    Why use this over Cohen's kappa: Krippendorff's alpha generalises to
    >2 raters, missing values, and ordinal/interval scales without changing
    the formula's interpretation. It also avoids the "kappa paradox" where
    highly-skewed marginals push kappa near zero even with high agreement.
    """
    if len(rater_a) != len(rater_b):
        raise ValueError(f"length mismatch: {len(rater_a)} vs {len(rater_b)}")
    n = len(rater_a)
    if n == 0:
        return 0.0
    for v in (*rater_a, *rater_b):
        if v not in (0, 1):
            raise ValueError(f"binary alpha requires 0/1 inputs; got {v}")

    # Observed disagreement: fraction of pairs that disagree.
    do = sum(1 for a, b in zip(rater_a, rater_b, strict=True) if a != b) / n

    # Expected disagreement under chance, using the pooled marginal.
    pooled = list(rater_a) + list(rater_b)
    m = len(pooled)  # total pooled values across both raters (== 2n)
    p1 = sum(pooled) / m
    p0 = 1 - p1
    # Nominal Krippendorff's alpha requires the finite-sample correction
    # m/(m-1) on the expected disagreement; without it (de = 2*p0*p1) alpha
    # is biased low at the small n typical of a judge-agreement check. The
    # correction vanishes as m grows, so it never hurts large samples.
    de = (2 * p0 * p1) * m / (m - 1) if m > 1 else 0.0

    if de == 0:
        return 1.0 if do == 0 else 0.0
    return 1 - do / de
