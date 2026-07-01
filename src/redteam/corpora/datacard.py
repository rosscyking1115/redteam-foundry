"""Markdown renderers for the corpus audit.

Two outputs, both plain Markdown strings (the CLI writes them to disk):

- `render_quality_report` — the full audit: composition, duplicate clusters,
  near-duplicate pairs, and label issues. For maintainers.
- `render_datacard` — a dataset "data card" in the style recommended for
  documenting ML datasets, summarising provenance and the audit's headline
  numbers. For anyone deciding whether to use the corpus.

Both quote only *truncated* prompt previews produced by `quality._preview`,
never full adversarial prompts.
"""

from __future__ import annotations

from collections.abc import Mapping

from redteam.corpora.quality import CorpusQualityReport


def _kv_table(title: str, counts: Mapping[str, int]) -> list[str]:
    rows = [f"### {title}", "", "| Key | Count |", "| --- | ---: |"]
    for key, val in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
        rows.append(f"| {key} | {val} |")
    rows.append("")
    return rows


def render_quality_report(report: CorpusQualityReport, *, title: str = "Corpus") -> str:
    """Render the full quality report as Markdown."""
    r = report
    out: list[str] = [
        f"# Corpus quality report — {title}",
        "",
        f"- **Cases:** {r.n_cases}",
        f"- **Exact-duplicate cases:** {r.n_exact_duplicate_cases} "
        f"({r.duplicate_rate:.1%} of corpus) in {r.n_exact_duplicate_groups} group(s); "
        f"{r.n_cross_source_duplicate_groups} span more than one source.",
        f"- **Near-duplicate pairs** (Jaccard ≥ {r.near_dup_threshold:.2f}): "
        f"{r.n_near_duplicate_pairs} ({r.n_cross_source_near_duplicate_pairs} cross-source).",
        f"- **Label/integrity issues:** {r.n_label_issues}",
        "",
        "Near-duplicate detection is a token-Jaccard heuristic, not a guarantee. "
        "Previews are truncated; full prompts live in the source corpora.",
        "",
    ]

    out += _kv_table("Cases by source", r.by_source)
    out += _kv_table("Cases by category", r.by_category)
    out += _kv_table("Cases by severity", r.by_severity)

    out += [
        "### Prompt length (chars)",
        "",
        "| min | median | mean | max |",
        "| ---: | ---: | ---: | ---: |",
        f"| {r.prompt_length.min} | {r.prompt_length.median:g} "
        f"| {r.prompt_length.mean:g} | {r.prompt_length.max} |",
        "",
    ]

    out += ["### Exact-duplicate groups", ""]
    if r.exact_duplicate_groups:
        out += ["| size | sources | cross-source | preview |", "| ---: | --- | :---: | --- |"]
        for g in r.exact_duplicate_groups:
            mark = "yes" if g.cross_source else ""
            out.append(f"| {g.size} | {', '.join(g.sources)} | {mark} | {g.preview} |")
    else:
        out.append("_None._")
    out.append("")

    out += ["### Near-duplicate pairs (top by similarity)", ""]
    if r.near_duplicate_pairs:
        out += [
            "| similarity | sources | cross | preview a | preview b |",
            "| ---: | --- | :---: | --- | --- |",
        ]
        for p in r.near_duplicate_pairs:
            srcs = p.source_a if p.source_a == p.source_b else f"{p.source_a} / {p.source_b}"
            mark = "yes" if p.cross_source else ""
            out.append(f"| {p.similarity:.3f} | {srcs} | {mark} | {p.preview_a} | {p.preview_b} |")
    else:
        out.append("_None above threshold._")
    out.append("")

    out += ["### Label / integrity issues", ""]
    if r.label_issues:
        out += ["| case id | source | issue |", "| --- | --- | --- |"]
        for issue in r.label_issues:
            out.append(f"| `{issue.case_id}` | {issue.source} | {issue.issue} |")
    else:
        out.append("_None._")
    out.append("")

    return "\n".join(out)


def render_datacard(
    report: CorpusQualityReport,
    *,
    title: str = "Corpus",
    sources_meta: Mapping[str, str] | None = None,
) -> str:
    """Render a dataset data card summarising provenance + audit headline.

    `sources_meta` maps a source name to a one-line provenance string (e.g.
    "AdvBench — Zou et al. 2023, MIT, pinned 098262e"); unknown sources fall
    back to just the name.
    """
    r = report
    meta = dict(sources_meta or {})
    out: list[str] = [
        f"# Corpus data card — {title}",
        "",
        "## Sources",
        "",
    ]
    for src in sorted(r.by_source):
        out.append(
            f"- **{src}** ({r.by_source[src]} cases) — {meta.get(src, 'see configs/dataset_versions.yaml')}"
        )
    out += [
        "",
        "## Composition",
        "",
        f"- Total cases: **{r.n_cases}**",
        f"- Categories: {', '.join(f'{k} ({v})' for k, v in sorted(r.by_category.items()))}",
        f"- Severity: {', '.join(f'{k} ({v})' for k, v in sorted(r.by_severity.items()))}",
        f"- Prompt length (chars): min {r.prompt_length.min}, "
        f"median {r.prompt_length.median:g}, mean {r.prompt_length.mean:g}, max {r.prompt_length.max}",
        "",
        "## Duplicate analysis",
        "",
        f"- Exact-duplicate cases: **{r.n_exact_duplicate_cases}** "
        f"({r.duplicate_rate:.1%}) across {r.n_exact_duplicate_groups} group(s).",
        f"- Cross-source duplicate groups: **{r.n_cross_source_duplicate_groups}** "
        "(the same prompt appearing in more than one upstream dataset).",
        f"- Near-duplicate pairs (Jaccard ≥ {r.near_dup_threshold:.2f}): "
        f"**{r.n_near_duplicate_pairs}**, of which {r.n_cross_source_near_duplicate_pairs} are cross-source.",
        "",
        "## Label quality",
        "",
        f"- Integrity issues found: **{r.n_label_issues}** (empty/trivial prompts, duplicate ids).",
        "- Language and attack-family tagging are **not yet applied** — see "
        "`docs/ROADMAP.md` (Phase 1b / Phase 4).",
        "",
        "## Known limitations",
        "",
        "- Near-duplicate detection is a token-Jaccard heuristic; it can miss "
        "paraphrases that share few tokens and over-flag heavily templated prompts.",
        "- Duplicate/overlap counts mean concatenating these corpora without "
        "de-duplication double-counts attack success — split or dedupe before "
        "reporting a single ASR over the union.",
        "",
        "## Unsafe content handling",
        "",
        "- Cases are post-exclusion-filter (CSAM / WMD-synthesis / detailed "
        "self-harm methods dropped at load time; see `ETHICS.md`).",
        "- This card and the quality report quote only truncated prompt "
        "previews, never full adversarial prompts.",
        "",
        "## Recommended use",
        "",
        "- Benchmark research and defence comparison.",
        "- **Not** a standalone safety certification, and not a deployment "
        "approval signal (see the README positioning).",
        "",
    ]
    return "\n".join(out)
