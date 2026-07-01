"""Corpus quality audit — the first foundry module.

Turns a stream of `AttackCase` objects into a structured quality report:
composition, prompt-length distribution, exact + near-duplicate clusters
(including duplicates that span *different* source corpora), and basic
label-integrity issues.

Why this exists
---------------
A red-team benchmark is only as good as the corpus behind it. Published
adversarial datasets overlap heavily — JailbreakBench derives behaviours from
AdvBench, HarmBench shares goals with both — so naively concatenating them
inflates the denominator and double-counts attack success. This module makes
that overlap measurable instead of invisible, and is the input to the
staleness scoring that follows (see `docs/ROADMAP.md`).

Design
------
- **Pure and stdlib-only.** `audit_corpus()` does no I/O and pulls in no
  heavy deps, so it is cheap to unit-test and deterministic. Rendering and
  file-writing live in `datacard.py` / the CLI.
- **Exact duplicates** are detected on a normalised form (casefold + collapsed
  whitespace), so trivial spacing/case variants cluster together.
- **Near duplicates** use token-set Jaccard similarity over the exact-dup
  *representatives*. This is an O(r^2) pass over the r unique prompts with a
  cheap length-ratio prune; it is a research heuristic, not a guarantee, and
  is labelled as such in the report.
"""

from __future__ import annotations

import re
import statistics
from collections import Counter
from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict, Field

from redteam.corpora.taxonomy import ATTACK_FAMILIES, detect_language, infer_attack_families
from redteam.schemas import AttackCase

# Tokeniser for near-duplicate Jaccard. Unicode word characters so CJK and
# accented scripts are not silently dropped (matters for the multilingual
# corpus on the roadmap).
_WORD = re.compile(r"\w+", re.UNICODE)
_WS = re.compile(r"\s+")

# A prompt this short (after stripping) is almost certainly a parsing artefact
# rather than a real adversarial prompt.
_TRIVIAL_PROMPT_CHARS = 8

# Default similarity at/above which two distinct prompts are "near duplicates".
_DEFAULT_NEAR_DUP_THRESHOLD = 0.85


def normalize_text(text: str) -> str:
    """Casefold + collapse whitespace. The key for exact-duplicate grouping."""
    return _WS.sub(" ", text.strip()).casefold()


def _tokens(text: str) -> frozenset[str]:
    return frozenset(m.group(0) for m in _WORD.finditer(text.casefold()))


def _jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _preview(text: str, *, limit: int = 60) -> str:
    """A short, single-line preview of a prompt for reports.

    Adversarial prompts come from published datasets, but we still avoid
    dumping them in full into a committed report — a truncated preview is
    enough to recognise a cluster without reproducing the whole attack.
    """
    flat = _WS.sub(" ", text.strip())
    return flat if len(flat) <= limit else flat[:limit].rstrip() + "…"


# ---------------------------------------------------------------------------
# Report models
# ---------------------------------------------------------------------------


class LengthStats(BaseModel):
    """Distribution of prompt lengths in characters."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    min: int = 0
    median: float = 0.0
    mean: float = 0.0
    max: int = 0


class DuplicateGroup(BaseModel):
    """A cluster of cases whose prompts are identical after normalisation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    size: int = Field(ge=2)
    case_ids: list[str]
    sources: list[str]
    cross_source: bool
    preview: str


class NearDuplicatePair(BaseModel):
    """Two distinct prompts with Jaccard similarity >= the threshold."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id_a: str
    id_b: str
    source_a: str
    source_b: str
    cross_source: bool
    similarity: float
    preview_a: str
    preview_b: str


class LabelIssue(BaseModel):
    """One integrity problem found on a single case."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    case_id: str
    source: str
    issue: str


class CorpusQualityReport(BaseModel):
    """Structured result of auditing a set of AttackCases."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    n_cases: int
    by_source: dict[str, int]
    by_category: dict[str, int]
    by_severity: dict[str, int]
    prompt_length: LengthStats

    # Exact duplicates (normalised-text identical).
    n_exact_duplicate_cases: int
    n_exact_duplicate_groups: int
    n_cross_source_duplicate_groups: int
    duplicate_rate: float
    exact_duplicate_groups: list[DuplicateGroup] = Field(default_factory=list)

    # Near duplicates (token Jaccard >= threshold, excluding exact dups).
    near_dup_threshold: float
    n_near_duplicate_pairs: int
    n_cross_source_near_duplicate_pairs: int
    near_duplicate_pairs: list[NearDuplicatePair] = Field(default_factory=list)

    # Language / script coverage (Phase 1b — script-based, coarse).
    language_coverage: dict[str, int] = Field(default_factory=dict)
    n_mixed_script: int = 0

    # Attack-family surface markers (Phase 1b — heuristic; a case may match
    # several families or none). `n_untagged_family` is the coverage gap.
    attack_family_coverage: dict[str, int] = Field(default_factory=dict)
    n_untagged_family: int = 0

    # Label / integrity issues.
    n_label_issues: int
    label_issues: list[LabelIssue] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------


def audit_corpus(
    cases: Sequence[AttackCase],
    *,
    near_dup_threshold: float = _DEFAULT_NEAR_DUP_THRESHOLD,
    max_groups_reported: int = 100,
    max_near_dup_pairs_reported: int = 200,
) -> CorpusQualityReport:
    """Audit a set of AttackCases. Pure: no I/O, deterministic.

    The `max_*_reported` caps bound how many examples are *listed* in the
    report; the counts (`n_exact_duplicate_cases`, `n_near_duplicate_pairs`,
    ...) always reflect the full corpus.
    """
    if not (0.0 < near_dup_threshold <= 1.0):
        raise ValueError(f"near_dup_threshold must be in (0,1]; got {near_dup_threshold}")

    n = len(cases)
    # str() coerces the Literal source/category/severity types to plain str so
    # the report's dict[str, int] fields type-check (Literal dicts are invariant).
    by_source = dict(Counter(str(c.source) for c in cases))
    by_category = dict(Counter(str(c.category) for c in cases))
    by_severity = dict(Counter(str(c.severity) for c in cases))

    lengths = [len(c.prompt) for c in cases]
    length_stats = (
        LengthStats(
            min=min(lengths),
            median=float(statistics.median(lengths)),
            mean=round(statistics.fmean(lengths), 1),
            max=max(lengths),
        )
        if lengths
        else LengthStats()
    )

    exact_groups, n_dup_cases, n_cross_groups = _exact_duplicates(cases, max_groups_reported)
    duplicate_rate = (n_dup_cases / n) if n else 0.0

    near_pairs, n_near_total, n_near_cross = _near_duplicates(
        cases, near_dup_threshold, max_near_dup_pairs_reported
    )

    label_issues = _label_issues(cases)

    # Language/script coverage and attack-family surface markers (Phase 1b).
    language_coverage: Counter[str] = Counter()
    n_mixed = 0
    family_coverage: Counter[str] = Counter({fam: 0 for fam in ATTACK_FAMILIES})
    n_untagged = 0
    for case in cases:
        tag = detect_language(case.prompt)
        language_coverage[tag.label] += 1
        if tag.mixed:
            n_mixed += 1
        families = infer_attack_families(case.prompt)
        if families:
            for fam in families:
                family_coverage[fam] += 1
        else:
            n_untagged += 1

    return CorpusQualityReport(
        n_cases=n,
        by_source=by_source,
        by_category=by_category,
        by_severity=by_severity,
        prompt_length=length_stats,
        n_exact_duplicate_cases=n_dup_cases,
        n_exact_duplicate_groups=sum(1 for _ in _iter_exact_groups(cases)),
        n_cross_source_duplicate_groups=n_cross_groups,
        duplicate_rate=round(duplicate_rate, 4),
        exact_duplicate_groups=exact_groups,
        near_dup_threshold=near_dup_threshold,
        n_near_duplicate_pairs=n_near_total,
        n_cross_source_near_duplicate_pairs=n_near_cross,
        near_duplicate_pairs=near_pairs,
        language_coverage=dict(language_coverage),
        n_mixed_script=n_mixed,
        attack_family_coverage=dict(family_coverage),
        n_untagged_family=n_untagged,
        n_label_issues=len(label_issues),
        label_issues=label_issues[:max_groups_reported],
    )


def _iter_exact_groups(cases: Sequence[AttackCase]) -> list[list[AttackCase]]:
    """Group cases by normalised prompt; return only groups with >= 2 members."""
    buckets: dict[str, list[AttackCase]] = {}
    for case in cases:
        buckets.setdefault(normalize_text(case.prompt), []).append(case)
    return [grp for grp in buckets.values() if len(grp) >= 2]


def _exact_duplicates(
    cases: Sequence[AttackCase], max_reported: int
) -> tuple[list[DuplicateGroup], int, int]:
    groups = _iter_exact_groups(cases)
    # Largest clusters first — those are the most worth looking at.
    groups.sort(key=len, reverse=True)

    n_dup_cases = sum(len(g) - 1 for g in groups)  # extras beyond the first
    n_cross = 0
    reported: list[DuplicateGroup] = []
    for grp in groups:
        sources = sorted({str(c.source) for c in grp})
        cross = len(sources) > 1
        if cross:
            n_cross += 1
        if len(reported) < max_reported:
            reported.append(
                DuplicateGroup(
                    size=len(grp),
                    case_ids=[c.id for c in grp],
                    sources=sources,
                    cross_source=cross,
                    preview=_preview(grp[0].prompt),
                )
            )
    return reported, n_dup_cases, n_cross


def _near_duplicates(
    cases: Sequence[AttackCase], threshold: float, max_reported: int
) -> tuple[list[NearDuplicatePair], int, int]:
    """Token-Jaccard near-duplicate pass over exact-dup representatives.

    O(r^2) over the r unique normalised prompts, with a length-ratio prune so
    wildly different prompts are skipped before the Jaccard is computed.
    """
    # One representative per exact-duplicate cluster, so near-dup work is done
    # on unique prompts only (and exact dups are not re-reported as near dups).
    seen: set[str] = set()
    reps: list[AttackCase] = []
    for case in cases:
        key = normalize_text(case.prompt)
        if key not in seen:
            seen.add(key)
            reps.append(case)

    tokens = [_tokens(c.prompt) for c in reps]
    lengths = [len(t) for t in tokens]

    pairs: list[NearDuplicatePair] = []
    n_total = 0
    n_cross = 0
    for i in range(len(reps)):
        ti, li = tokens[i], lengths[i]
        if li == 0:
            continue
        for j in range(i + 1, len(reps)):
            lj = lengths[j]
            if lj == 0:
                continue
            # Length-ratio prune: two sets can't reach the Jaccard threshold
            # if their sizes are too far apart (|A∩B| <= min(|A|,|B|), and
            # Jaccard <= min/max), so skip before the expensive intersection.
            if min(li, lj) / max(li, lj) < threshold:
                continue
            sim = _jaccard(ti, tokens[j])
            if sim >= threshold:
                n_total += 1
                cross = reps[i].source != reps[j].source
                if cross:
                    n_cross += 1
                if len(pairs) < max_reported:
                    pairs.append(
                        NearDuplicatePair(
                            id_a=reps[i].id,
                            id_b=reps[j].id,
                            source_a=reps[i].source,
                            source_b=reps[j].source,
                            cross_source=cross,
                            similarity=round(sim, 3),
                            preview_a=_preview(reps[i].prompt),
                            preview_b=_preview(reps[j].prompt),
                        )
                    )
    # Most-similar first for the reported subset.
    pairs.sort(key=lambda p: p.similarity, reverse=True)
    return pairs, n_total, n_cross


def _label_issues(cases: Sequence[AttackCase]) -> list[LabelIssue]:
    """Integrity checks the Pydantic schema cannot enforce on its own."""
    issues: list[LabelIssue] = []
    id_counts = Counter(c.id for c in cases)
    seen_dup_id: set[str] = set()
    for case in cases:
        stripped = case.prompt.strip()
        if not stripped:
            issues.append(LabelIssue(case_id=case.id, source=case.source, issue="empty prompt"))
        elif len(stripped) < _TRIVIAL_PROMPT_CHARS:
            issues.append(
                LabelIssue(
                    case_id=case.id,
                    source=case.source,
                    issue=f"prompt under {_TRIVIAL_PROMPT_CHARS} chars",
                )
            )
        if id_counts[case.id] > 1 and case.id not in seen_dup_id:
            seen_dup_id.add(case.id)
            issues.append(
                LabelIssue(
                    case_id=case.id,
                    source=case.source,
                    issue=f"duplicate case id ({id_counts[case.id]}x)",
                )
            )
    return issues
