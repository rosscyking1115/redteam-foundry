# Tests — which claim each suite defends

Every test module opens with a one-line `Defends:` header naming the claim (or
published number) it protects. This file is the index: it maps each suite to the
claim it defends and, where relevant, to the section of
[`METHODOLOGY.md`](../METHODOLOGY.md) or the
[benchmark-quality report card](../docs/findings/benchmark-quality-report-card.md)
that depends on it. Run everything with `pytest tests/unit`.

The point of the mapping is legibility: a reviewer should be able to go from "do
I believe the 0–4% headline?" to the exact test that keeps the machinery behind
it honest, without reading the whole suite.

## Ethics & safety (merge-blocking)

| Suite | Defends |
| --- | --- |
| [`test_exclusion_filter.py`](unit/test_exclusion_filter.py) | The ETHICS exclusion filter — excluded categories are dropped at corpus-load time, before any prompt reaches a model or artifact. **If red, do not merge.** |
| [`test_packs.py`](unit/test_packs.py) | The challenge-pack exporter redacts adversarial prompts by default — an ETHICS guarantee and the downstream consume contract. |
| [`test_budget.py`](unit/test_budget.py) | The hard USD budget cap that stops a run from overspending on paid APIs. |
| [`test_hardening.py`](unit/test_hardening.py) | Budget reservation under concurrency, guard fail-closed, and defence delimiter neutralisation. |

## Measurement core — the ASR pipeline (METHODOLOGY §5–§8)

| Suite | Defends |
| --- | --- |
| [`test_orchestrator.py`](unit/test_orchestrator.py) | The orchestrator runs cases through a defence stack and aggregates ASR correctly — the core measurement path. |
| [`test_orchestrator_score.py`](unit/test_orchestrator_score.py) | The scoring path applies the judge to a run and aggregates verdicts into run-level ASR. |
| [`test_judge_claude.py`](unit/test_judge_claude.py) | The LLM judge returns a well-formed structured verdict — the primary scorer behind every published ASR (§6). |
| [`test_scorer_refusal.py`](unit/test_scorer_refusal.py) | The rule-based refusal detector stays a cheap *pre-screen* only — never a published number (§6). |
| [`test_defences_base.py`](unit/test_defences_base.py) | Defences compose and wrap a target without changing its `send()` contract (§4). |
| [`test_targets_mocked.py`](unit/test_targets_mocked.py) | Each target adapter honours the shared cache/budget contract, transport mocked. |

## Validation & statistics — how much to trust the numbers (METHODOLOGY §7, §9)

| Suite | Defends |
| --- | --- |
| [`test_orchestrator_cross_judge.py`](unit/test_orchestrator_cross_judge.py) | The cross-judge path computes inter-judge agreement (Cohen's kappa / Krippendorff's alpha) — the headline validation mechanism (§7). |
| [`test_stats.py`](unit/test_stats.py) | The bootstrap confidence intervals and the Krippendorff's-alpha / kappa helpers — every CI and agreement number traces here. |
| [`test_judge_human.py`](unit/test_judge_human.py) | The human spot-check export and the Cohen's-kappa helper used as a tertiary check. |

## Corpus audit & taxonomy — the quality findings (report card §1)

| Suite | Defends |
| --- | --- |
| [`test_corpus_quality.py`](unit/test_corpus_quality.py) | The corpus-audit metrics (exact/near-duplicate, language, attack-family, label integrity) behind the quality scorecard. |
| [`test_taxonomy.py`](unit/test_taxonomy.py) | Language/script detection and attack-family inference — the coverage axes the audit reports. |
| [`test_huggingface.py`](unit/test_huggingface.py) | The `corpora audit-hf` row mapping, so any Hugging Face dataset audits into the same canonical schema. |
| [`test_staleness.py`](unit/test_staleness.py) | The staleness heuristic and its broken-out components (universal-low-ASR, defence-insensitivity, judge-disagreement). |

## Over-refusal / defence comparison — the "free but useless" finding (report card §3)

| Suite | Defends |
| --- | --- |
| [`test_compare.py`](unit/test_compare.py) | The defence-comparison table (ASR, false-refusal, safe-usefulness, cost). |
| [`test_benign.py`](unit/test_benign.py) | The benign control set is well-formed and labelled, so FRR / safe-usefulness over it are meaningful. |
| [`test_multilingual.py`](unit/test_multilingual.py) | The multilingual benign set and per-language false-refusal breakdown. |

## Corpora, schemas & infrastructure (METHODOLOGY §2, §10)

| Suite | Defends |
| --- | --- |
| [`test_loaders.py`](unit/test_loaders.py) | Each corpus loader parses its source into the canonical case schema (§2). |
| [`test_agentdojo_loader.py`](unit/test_agentdojo_loader.py) | The AgentDojo indirect-injection corpus loads and pins correctly (the §8 AgentDojo cells). |
| [`test_schemas.py`](unit/test_schemas.py) | The canonical run/case schemas validate their invariants. |
| [`test_cache.py`](unit/test_cache.py) | The response cache is content-addressed and deterministic — the basis for "re-runs are free and reproduce the numbers exactly" (§10). |
| [`test_pricing.py`](unit/test_pricing.py) | Token pricing is correct, so the real-USD cost reported per run is honest. |
| [`test_inspect_export.py`](unit/test_inspect_export.py) | Every run exports to a valid UK AISI Inspect eval log — the interoperability claim (§10). |
| [`test_smoke.py`](unit/test_smoke.py) | The package imports and the CLI is wired — the install/version claim. |
