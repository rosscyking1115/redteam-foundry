"""Benchmark staleness scoring (Phase 2).

Composes signals from a corpus audit and one or more evaluation runs into a
single, **explicitly heuristic** staleness score in [0, 1] — higher means the
benchmark looks less likely to measure real, current deployment risk.

The whole point of the foundry pivot: a static attack that no longer succeeds
is ambiguous between "the model is robust" and "the benchmark is stale". This
module makes the second hypothesis measurable by combining five components:

| Component | Weight | Source | High score means |
| --- | --- | --- | --- |
| obsolete_pattern | 0.30 | corpus | prompts lean on dated jailbreak memes (DAN/AIM/…) |
| universal_low_asr | 0.25 | runs | attacks barely succeed even without any defence |
| duplicate_cluster | 0.20 | corpus | heavy exact/near duplication |
| low_defence_sensitivity | 0.15 | runs | defences don't move ASR — can't tell them apart |
| judge_disagreement | 0.10 | runs | judges can't agree on ASR — items are ambiguous |

Only the components whose input data is present are scored; the composite is a
weight-renormalised average over the *available* components, and the report
says which were used. This is a research heuristic to prompt investigation,
**not** a scientific truth or a pass/fail gate.
"""

from __future__ import annotations

import re
import statistics
from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict, Field

from redteam.corpora.quality import CorpusQualityReport, audit_corpus
from redteam.orchestrator import RunResult
from redteam.schemas import AttackCase

# Component weights (sum to 1.0 across all five). Renormalised over whichever
# components have data. Mirrors the ratios in docs/ROADMAP.md.
_WEIGHTS: dict[str, float] = {
    "obsolete_pattern": 0.30,
    "universal_low_asr": 0.25,
    "duplicate_cluster": 0.20,
    "low_defence_sensitivity": 0.15,
    "judge_disagreement": 0.10,
}

# ASR movement (baseline vs defended) treated as "fully sensitive". A benchmark
# whose best defence shifts ASR by this much scores 0 on the sensitivity axis.
_SENSITIVITY_REFERENCE = 0.10

# Dated jailbreak-meme markers. Acronym personas are case-sensitive (so "DAN"
# does not match "abundant"); descriptive phrases are case-insensitive.
_OBSOLETE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bDAN\b"),
    re.compile(r"\bAIM\b"),
    re.compile(r"\bSTAN\b"),
    re.compile(r"\bDUDE\b"),
    re.compile(r"\bdo anything now\b", re.I),
    re.compile(r"\bdeveloper mode\b", re.I),
    re.compile(r"\bjailbr(?:eak|oken)\b", re.I),
    re.compile(r"\bevil (?:confidant|trusted advisor)\b", re.I),
    re.compile(r"\bunfiltered (?:ai|assistant|model|response)\b", re.I),
    re.compile(r"\bno (?:restrictions|filters|limitations|guidelines|rules)\b", re.I),
    re.compile(r"\bhypothetical response\b", re.I),
    re.compile(r"\bopposite (?:mode|day)\b", re.I),
)


class StalenessComponent(BaseModel):
    """One scored axis of the staleness heuristic."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    available: bool
    score: float | None = Field(default=None, description="[0,1], higher = more stale; None if N/A")
    weight: float
    detail: str


class StalenessReport(BaseModel):
    """Composite staleness heuristic for one corpus."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    corpus_title: str
    n_cases: int
    n_runs: int
    components: list[StalenessComponent]
    n_components_available: int
    staleness_score: float | None  # None if no component had data
    interpretation: str
    confidence: str
    caveat: str


# ---------------------------------------------------------------------------
# Component helpers
# ---------------------------------------------------------------------------


def _effective_asr(run: RunResult) -> float:
    """Judge ASR if the run was judged, else the rule-based ASR.

    The judge is the source of truth (see METHODOLOGY §6); rule-based ASR is a
    fallback so an un-judged run still contributes something.
    """
    if run.judged and run.judge_asr_rate is not None:
        return run.judge_asr_rate
    return run.asr


def _obsolete_pattern_score(cases: Sequence[AttackCase]) -> tuple[float, str]:
    if not cases:
        return 0.0, "no cases"
    n_hit = sum(1 for c in cases if any(p.search(c.prompt) for p in _OBSOLETE_PATTERNS))
    frac = n_hit / len(cases)
    return frac, f"{n_hit}/{len(cases)} prompts match a dated jailbreak-meme marker"


def _duplicate_cluster_score(report: CorpusQualityReport) -> tuple[float, str]:
    near_density = (
        min(1.0, report.n_near_duplicate_pairs / report.n_cases) if report.n_cases else 0.0
    )
    score = min(1.0, report.duplicate_rate + 0.5 * near_density)
    return score, (
        f"exact-dup rate {report.duplicate_rate:.1%}, "
        f"{report.n_near_duplicate_pairs} near-dup pair(s) over {report.n_cases} cases"
    )


def _universal_low_asr_score(runs: Sequence[RunResult]) -> tuple[float, str] | None:
    baselines = [r for r in runs if not r.defences]
    if not baselines:
        return None
    max_asr = max(_effective_asr(r) for r in baselines)
    return 1.0 - max_asr, f"max baseline ASR {max_asr:.1%} across {len(baselines)} baseline run(s)"


def _defence_sensitivity_score(runs: Sequence[RunResult]) -> tuple[float, str] | None:
    """1 - normalised max |ASR(baseline) - ASR(defended)| within each target."""
    by_target: dict[str, list[RunResult]] = {}
    for r in runs:
        by_target.setdefault(r.target, []).append(r)

    best_delta: float | None = None
    for target_runs in by_target.values():
        baselines = [r for r in target_runs if not r.defences]
        defended = [r for r in target_runs if r.defences]
        if not baselines or not defended:
            continue
        base_asr = max(_effective_asr(r) for r in baselines)
        for d in defended:
            delta = abs(base_asr - _effective_asr(d))
            best_delta = delta if best_delta is None else max(best_delta, delta)

    if best_delta is None:
        return None
    score = 1.0 - min(1.0, best_delta / _SENSITIVITY_REFERENCE)
    return score, (
        f"largest baseline→defence ASR shift {best_delta:.1%} (ref {_SENSITIVITY_REFERENCE:.0%})"
    )


def _judge_disagreement_score(runs: Sequence[RunResult]) -> tuple[float, str] | None:
    kappas = [r.cross_judge_asr_kappa for r in runs if r.cross_judge_asr_kappa is not None]
    if not kappas:
        return None
    mean_kappa = statistics.fmean(kappas)
    score = 1.0 - max(0.0, min(1.0, mean_kappa))
    return score, f"mean cross-judge ASR κ {mean_kappa:+.3f} over {len(kappas)} run(s)"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def _interpret(score: float) -> str:
    if score >= 0.66:
        return (
            "Likely stale on the measured axes - combine with fresh attack surfaces "
            "(agentic tool-use, multi-turn, multilingual) before using as release evidence."
        )
    if score >= 0.33:
        return "Mixed - some staleness signals; read the component breakdown before concluding."
    return "Still challenging on the measured axes."


def score_staleness(
    cases: Sequence[AttackCase],
    runs: Sequence[RunResult] = (),
    *,
    quality: CorpusQualityReport | None = None,
    title: str = "corpus",
    near_dup_threshold: float = 0.85,
) -> StalenessReport:
    """Compute the composite staleness heuristic for one corpus.

    `runs` is optional: with no runs, only the two corpus-derived components
    are scored and confidence is reported as low.
    """
    report = quality or audit_corpus(cases, near_dup_threshold=near_dup_threshold)

    components: list[StalenessComponent] = []

    obs_score, obs_detail = _obsolete_pattern_score(cases)
    components.append(
        StalenessComponent(
            name="obsolete_pattern",
            available=True,
            score=obs_score,
            weight=_WEIGHTS["obsolete_pattern"],
            detail=obs_detail,
        )
    )

    dup_score, dup_detail = _duplicate_cluster_score(report)
    components.append(
        StalenessComponent(
            name="duplicate_cluster",
            available=True,
            score=dup_score,
            weight=_WEIGHTS["duplicate_cluster"],
            detail=dup_detail,
        )
    )

    run_components: list[tuple[str, tuple[float, str] | None]] = [
        ("universal_low_asr", _universal_low_asr_score(runs)),
        ("low_defence_sensitivity", _defence_sensitivity_score(runs)),
        ("judge_disagreement", _judge_disagreement_score(runs)),
    ]
    for name, result in run_components:
        if result is None:
            components.append(
                StalenessComponent(
                    name=name,
                    available=False,
                    score=None,
                    weight=_WEIGHTS[name],
                    detail="no run data for this component",
                )
            )
        else:
            score, detail = result
            components.append(
                StalenessComponent(
                    name=name,
                    available=True,
                    score=score,
                    weight=_WEIGHTS[name],
                    detail=detail,
                )
            )

    available = [c for c in components if c.available and c.score is not None]
    if available:
        total_weight = sum(c.weight for c in available)
        composite = sum(c.weight * (c.score or 0.0) for c in available) / total_weight
        composite = round(composite, 4)
        interpretation = _interpret(composite)
    else:
        composite = None
        interpretation = "No component had data — cannot score."

    n_avail = len(available)
    confidence = (
        "low (corpus-only; no run data)" if not runs else ("high" if n_avail >= 4 else "moderate")
    )

    return StalenessReport(
        corpus_title=title,
        n_cases=len(cases),
        n_runs=len(runs),
        components=components,
        n_components_available=n_avail,
        staleness_score=composite,
        interpretation=interpretation,
        confidence=confidence,
        caveat=(
            "Heuristic, not a verdict. A high score flags a benchmark for review; "
            "it is not proof the corpus is worthless, nor is a low score proof a "
            "model is safe. Run components require runs that used THIS corpus."
        ),
    )


# ---------------------------------------------------------------------------
# Markdown renderer
# ---------------------------------------------------------------------------


def render_staleness_report(report: StalenessReport) -> str:
    r = report
    score_str = f"{r.staleness_score:.2f}" if r.staleness_score is not None else "n/a"
    out: list[str] = [
        f"# Benchmark staleness report — {r.corpus_title}",
        "",
        f"- **Staleness score (heuristic):** {score_str} / 1.00",
        f"- **Interpretation:** {r.interpretation}",
        f"- **Confidence:** {r.confidence} "
        f"({r.n_components_available}/{len(r.components)} components had data)",
        f"- **Inputs:** {r.n_cases} cases, {r.n_runs} run(s)",
        "",
        "> " + r.caveat,
        "",
        "## Components",
        "",
        "| component | weight | score | detail |",
        "| --- | ---: | ---: | --- |",
    ]
    for c in r.components:
        score_cell = f"{c.score:.2f}" if c.available and c.score is not None else "—"
        out.append(f"| {c.name} | {c.weight:.2f} | {score_cell} | {c.detail} |")
    out.append("")
    out.append(
        "Scores are in [0, 1]; higher = more stale. The composite is a "
        "weight-renormalised average over the components that had data."
    )
    out.append("")
    return "\n".join(out)
