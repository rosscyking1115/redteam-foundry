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

**This index is complete, and [`test_test_index.py`](unit/test_test_index.py)
enforces it.** The claim above — that the file maps *each* suite — used to be an
attestation with nothing behind it, and it was wrong: ten suites were missing.
A completeness claim nobody checks is this repository's own
attestation-is-not-enforcement finding, in its own test documentation. Adding a
test file without a row here now fails.

## Test conventions

Two rules, both earned rather than assumed.

**1. A test module opens with `Defends:`** — one line naming the claim or
published number it protects.

**2. A test that asserts a failure must assert *which* failure.** Not that
something went red — which thing, by message, by exception match, or by the
specific counter that moved. The rule exists because a guard once failed for the
wrong reason and looked identical to a guard working: the figure-caption guard
could not read a `κ` in a UTF-8 PNG chunk, so it rejected the retracted caption
as *unreadable metadata* rather than as a retracted claim. It was one small
change away from passing blind, and only the failure *message* revealed it. In
practice:

- `pytest.raises(SomeError)` needs `match=` whenever more than one defect can
  raise `SomeError` from the same call — which is nearly always, and always for
  `ValidationError`.
- A break-test that feeds bad input to a guard asserts the content of the
  complaint, not merely that a complaint exists.
- A guard that can pass vacuously carries a non-vacuity assertion: that the scan
  saw targets, that the dictionary set is non-empty, that the claim list is not
  empty. "0 problems found" and "nothing was examined" are otherwise the same
  output.

Written up as instance #16 and checklist item 20 in
[`what-does-this-metric-return-when-nothing-happened.md`](../docs/findings/what-does-this-metric-return-when-nothing-happened.md).

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
| [`test_stats.py`](unit/test_stats.py) | The bootstrap confidence intervals, the Krippendorff's-alpha / kappa helpers, and the grounding diagnostic — every CI, agreement and capability-gate number traces here. Includes the case a liveness check scores 100% and grounding scores 0. |
| [`test_controls.py`](unit/test_controls.py) | That a control harness can never be mistaken for a defence — registries disjoint, the `control:` marker reaching the artifact, and control runs excluded from corpus analysis rather than reclassified (§12.7). |
| [`test_judge_human.py`](unit/test_judge_human.py) | The human spot-check export and the Cohen's-kappa helper used as a tertiary check. |
| [`test_headline_table.py`](unit/test_headline_table.py) | That a published cross-judge kappa is only claimed as agreement when the labels actually varied — 11 of the 12 matrix cells are degenerate 0/0 and the claim rests on the positive control (§7) — and that the FAILED AgentDojo control stays in the frozen record (§12.6). |
| [`test_figure_caption.py`](unit/test_figure_caption.py) | That the same correction holds *inside the headline figure*: the caption drawn into `docs/results_matrix.png` makes no judge-agreement claim, and the committed image agrees with the generator that should have produced it. A figure is a claim, and this is the surface where a retracted one survived two releases because every check only confirmed the image loaded. |

## Corpus audit & taxonomy — the quality findings (report card §1)

| Suite | Defends |
| --- | --- |
| [`test_corpus_quality.py`](unit/test_corpus_quality.py) | The corpus-audit metrics (exact/near-duplicate, language, attack-family, label integrity) behind the quality scorecard. |
| [`test_taxonomy.py`](unit/test_taxonomy.py) | Language/script detection and attack-family inference — the coverage axes the audit reports. |
| [`test_huggingface.py`](unit/test_huggingface.py) | The `corpora audit-hf` row mapping, so any Hugging Face dataset audits into the same canonical schema. |
| [`test_staleness.py`](unit/test_staleness.py) | The staleness heuristic and its broken-out components (universal-low-ASR, defence-insensitivity, judge-disagreement). |
| [`test_readability.py`](unit/test_readability.py) | That "found nothing" and "could not read the input" stay distinguishable. The single primitive behind the alphabet screens in the refusal scorer, the near-duplicate pass, the staleness meme axis and the attack-family tagger — including the direction that matters most, that readable input is untouched. |

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
| [`test_dataset_pins.py`](unit/test_dataset_pins.py) | `configs/dataset_versions.yaml`'s own rule that loaders MUST resolve to its recorded commits — checked per loader and in both directions. Until now nothing read that file, so the corpus provenance published in §10 rested on a written record rather than a check. |
| [`test_schemas.py`](unit/test_schemas.py) | The canonical run/case schemas validate their invariants. |
| [`test_cache.py`](unit/test_cache.py) | The response cache is content-addressed and deterministic — the basis for "re-runs are free and reproduce the numbers exactly" (§10). |
| [`test_pricing.py`](unit/test_pricing.py) | Token pricing is correct, so the real-USD cost reported per run is honest. |
| [`test_inspect_export.py`](unit/test_inspect_export.py) | Every run exports to a valid UK AISI Inspect eval log — the interoperability claim (§10). |
| [`test_smoke.py`](unit/test_smoke.py) | The package imports and the CLI is wired — the install/version claim. |
| [`test_opencc_pin.py`](unit/test_opencc_pin.py) | The OpenCC treatment is defined by dictionary *content*, not by a package name — so an upgrade cannot silently change the conversion the locale-provenance study measured. |
| [`test_provenance.py`](unit/test_provenance.py) | That `s2twp`, not `s2tw`, is the dictionary-localisation condition, and that round-trip rendering preserves intent mechanically. If this inverts, condition B collapses into A and the study reports a null caused by a config choice. |

## Publication surface — what reaches a reader

These defend claims that live *outside* the measurement core: on the PyPI page,
in the published artifact, in the release workflow. They were the suites missing
from this index when the completeness claim was first enforced — which is itself
the pattern they exist to catch, since the publication surface is exactly where
an unchecked claim reaches someone.

| Suite | Defends |
| --- | --- |
| [`test_readme_links.py`](unit/test_readme_links.py) | No link or image in `README.md` is relative. The README *is* the PyPI `long_description`, and PyPI resolves no relative target — so a link GitHub renders fine is a dead link, or a broken headline figure, on the published page. |
| [`test_sdist_contents.py`](unit/test_sdist_contents.py) | The published sdist contains only files git tracks. An sdist is built from the *directory*, so a file hidden by a contributor's global gitignore is invisible to `git status`, to review, to CI — and packaged anyway. Publication is permanent. |
| [`test_release_gate.py`](unit/test_release_gate.py) | The release path gates rather than merely building and uploading: the suite runs before the upload via `needs:`, the tagged commit is reachable from `main`, and only the publishing job may mint an OIDC token. |
| [`test_version.py`](unit/test_version.py) | `redteam version` reports the version actually installed. Exists because it failed: 0.4.0 shipped metadata saying 0.4.0 beside code saying 0.3.0, with a green test that held the same wrong number. |
| [`test_release_heading.py`](unit/test_release_heading.py) | The top-most `CHANGELOG.md` heading agrees with the version being published and the day it is published on — the check `publish.yml` runs in its gate job. The heading is what a reader sees on PyPI, and a PyPI description is frozen at upload. |
| [`test_test_index.py`](unit/test_test_index.py) | The completeness claim in this file — that it maps every suite. It did not. |

## Absence & control discipline — that a null means something

| Suite | Defends |
| --- | --- |
| [`test_absence_detector.py`](unit/test_absence_detector.py) | That a 0.00% absence rate is evidence — by firing the detector at blank, whitespace-only, unparseable and missing cells and asserting *which* counter moves. A counter that cannot return non-zero reports the same 0.00% as a healthy run. |
| [`test_detector_control_verdict.py`](unit/test_detector_control_verdict.py) | That the only branch which condemns the AgentDojo arm requires affirmative evidence and cannot fire on a healthy run. Pre-registered, so these tests are what stop the boundary moving once a number exists (§12.7). |

## Live smoke — gated behind `RUN_LIVE=1`, not part of `pytest tests/unit`

These make real API calls and cost money, so they are excluded from the default
run and from CI. They are indexed because the index claims to be complete, and
an unlisted suite is indistinguishable from an absent one.

| Suite | Defends |
| --- | --- |
| [`test_targets_live.py`](smoke/test_targets_live.py) | Phase 2 acceptance: each target returns a sane response to a trivial prompt, cost tracking rolls up, and the second run is a cache hit. |
| [`test_defences_live.py`](smoke/test_defences_live.py) | Phase 3 exit criterion: a 20-case AdvBench subset through the bare target and through the prompt-only defence stack behaves as specified. |
