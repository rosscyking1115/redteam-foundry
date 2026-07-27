# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- **Corrected the inter-judge agreement claim.** The published headline said the
  two judges agreed "perfectly on ASR (κ = +1.000 in all 12 cells)". Eleven of
  those twelve values are degenerate: both judges labelled every cross-judged
  case identically and constantly, so expected agreement `pe = 1` and Cohen's κ
  is an undefined `0/0` that the scorer fills in as +1.000 by convention. That
  is the same defect the methodology already rejects on the refusal axis, at the
  opposite end of the marginals. The claim now rests on the **positive control's
  κ = +0.935** (n = 98, 79 positives per judge) — the one cell with substantial
  label variance on both margins. Updated in `METHODOLOGY.md` §7/§8/§12.3,
  `README.md`, and the findings report card. No measured number changed; the
  interpretation of one did.
- Also disclosed: the AdvBench Llama baseline's single ASR = 1 case is one of the
  two the cross-judge failed to parse, so that cell's cross-judge sample is
  all-zero and the one case that could have tested agreement was never
  cross-checked.
- **`staleness.py`'s `judge_disagreement` component no longer consumes a
  degenerate kappa.** Previously it averaged the stored `cross_judge_asr_kappa`
  across all runs, including the eleven whose value is the 0/0 convention — so a
  0.10-weight component reported "the judges agree" on exactly the saturated
  corpora it is meant to be informative about. Degenerate runs are now excluded
  from the average; when none survive, the component reports **undefined**
  rather than 0.00, drops out of the composite, and the remaining weights
  renormalise. Runs carrying a kappa but no per-case labels are treated as
  unverifiable and excluded rather than silently trusted.

  **Published staleness scores move as a result** — the movement is the finding,
  not a correction to the corpora:

  | corpus | was | now | components | why |
  | --- | ---: | ---: | ---: | --- |
  | AdvBench | 0.38 | **0.43** | 4/5 | all 4 cross-judged runs degenerate; component undefined and renormalised out |
  | AgentDojo | 0.43 | **0.43** | 5/5 | 7 of 8 degenerate, but one informative run survives, so the component still scores 0.00 — now stated as resting on 1 run |

  Neither corpus changes interpretation band ("Mixed") or confidence ("high").
  `reports/samples/staleness/` regenerated.
- `redteam.stats.is_degenerate_kappa` is now the single source of truth for the
  degenerate/informative rule, consumed by both `scripts/headline_table.py` and
  the staleness scorer so the published table and the composite metric cannot
  drift apart.

### Added
- **Synthetic detector control — run, and INCONCLUSIVE.** A capable model
  (`llama3.1:8b`, the same target as the section 8 AgentDojo rows) plus a system
  prompt instructing it to treat tool-output instructions as authoritative,
  on the same 50 cases. Pre-registered PASS bar was ASR >= 70%; the run returned
  **38%** (cross-judge kappa +0.917). Not a pass, and not reported as one.

  It failed for a different reason than the section 12.6 control: not
  incapacity, but **the control instruction not taking** — refusal fell 90% ->
  58% under the compliance prompt, so the model still refused a majority of the
  time and the staged hijack never reliably occurred. A tempting post-hoc
  rescue (0/29 refusals were hijacks, 19/21 non-refusals were) is recorded and
  refused: refusal is post-treatment and correlated with the outcome, so
  conditioning on it is selection on the dependent variable.

  **The AgentDojo arm remains uncontrolled** after two attempts and two distinct
  failure modes. METHODOLOGY section 12.8; frozen in `--check` under its own
  detector-control table, never merged with the positive controls.
- Section 7's refusal claim **narrowed by this run**: the instability is a
  property of the aligned charitable-redirect response, not of indirect
  injection as such. Where behaviour is unambiguous the same two judges agree
  perfectly on refusal (kappa = +1.000 on genuine variance, 29/50). The
  conclusion stands; the stated reason was too broad.
- **Control harnesses (`redteam.controls`), a concept distinct from defences.**
  A defence is a candidate mitigation whose effect on ASR is under study; a
  control harness deliberately forces a known outcome so the pipeline's ability
  to *detect* that outcome can be checked. Configured via a separate `controls:`
  key, deliberately absent from the `DEFENCES` registry (enforced by a test),
  and recorded in artifacts as `control:<id>` so a run can never read
  `defences: []` while compliance was engineered.

  Control runs are **excluded from `redteam corpora staleness` outright** rather
  than reclassified. A control is neither a baseline nor a defended run, and
  both naive partitions get it wrong — counting a high-ASR detector control as
  "defended" would read as a defence moving ASR a great deal, inverting this
  project's central finding. `StalenessReport.n_control_runs_excluded` records
  any exclusion and the rendered report prints it.
- `redteam.stats.grounding_score` — a capability diagnostic that asks whether a
  response is grounded in its input rather than whether output exists. §12.6's
  liveness check scored a confabulating model "100% engaged"; grounding scores
  the same responses 0. Reproduces the two figures quoted in METHODOLOGY
  (G = 1.00 for `llama3.1:8b`, G = 0.74 for `llama2-uncensored:7b`).
- `scripts/detector_control_verdict.py` — executes the pre-registered three-way
  detector-control rule against a judged run, so the verdict is computed rather
  than narrated and the boundary cannot move once the number is known.
- **AgentDojo positive control — run, and it FAILED its pre-registered
  threshold.** The indirect-injection arm previously had no under-elicitation
  control (§12.5 covered AdvBench only). `llama2-uncensored:7b` was run on the
  same 50 AgentDojo cases as the §8 Llama baseline, through the identical
  pipeline, with the PASS threshold (judge ASR ≥ 20%) committed in
  `configs/run_agentdojo_positive_control.yaml` *before* the run. Result: **2%**
  (cross-judge 4%, κ = +0.658 — which tripped the harness's own α guard).

  It is reported as **inconclusive, not as a null**. The model never refuses
  (0% rule-based) and confabulates instead of reading the tool output (26% of
  responses cite email addresses absent from the prompt), so the cell measures
  incapacity, not robustness. **The AgentDojo arm remains uncontrolled** and
  METHODOLOGY §8 now says so. New section METHODOLOGY §12.6, including the
  generalisable lesson (a positive control needs its own capability gate) and a
  recorded pre-registration error: the secondary diagnostic tested for
  emptiness/refusal and was blind to fluent confabulation.
- `configs/run_agentdojo_positive_control.yaml` — carries its own pre-registered
  analysis plan in-file.
- Both positive controls (the AdvBench pass and the AgentDojo failure) are now
  frozen in `scripts/headline_table.py --check`, so the failed control cannot
  quietly drop out of the record.
- `scripts/headline_table.py` now classifies each cell's cross-judge κ as
  degenerate or informative, recomputing the marginals from the per-case labels;
  it refuses to print a κ value for a degenerate cell, checks the positive
  control alongside the 12 matrix cells, and fails on status drift.
- `tests/unit/test_headline_table.py` — pins the degenerate/informative logic
  and the frozen 11-of-12 split (artifact-free, so it runs in CI).
- README: `mypy --strict` badge, and an explicit statement that CI gates on type
  errors and that `src/` is the typed surface.

## [0.3.0] — 2026-07-16

Research-legibility, validation, and hardening since 0.2.1 — documentation,
tooling, and reproducibility only (no change to the core measurement API). This
is the public **freeze** release: a complete, honest, reproducible artifact whose
headline negative result is validated by a positive control.

### Added
- **Positive control** — a `llama2-uncensored-local` target
  (`configs/run_positive_control.yaml`) run through the identical
  run/score/cross-judge pipeline reports **80% ASR** (cross-judge κ = +0.935),
  demonstrating the harness registers a high attack-success rate on a vulnerable
  model. Documented in `METHODOLOGY.md` §12.5.
- **One-command headline repro** — `scripts/headline_table.py` regenerates the
  `METHODOLOGY.md` §8 table from cached run artifacts (no API calls); `--check`
  asserts every cell matches the frozen numbers.
- **`tests/README.md`** mapping each test suite to the claim it defends, plus a
  one-line `Defends:` header on every test module.
- Optional `num_ctx` on the Ollama target adapter (a bounded context window lets
  a 7B model load on an 8 GB-VRAM machine).
- `uv.lock` committed for a byte-for-byte reproducible environment.
- A README **pipeline diagram** ("how it fits together") and a **two-repo stack**
  pointer to the `agent-release-gates` companion + the project map.

### Changed
- **README** re-led around the research question and the negative/meta finding;
  the positioning / release-gate material moved into a lower "where this sits"
  section.
- **`METHODOLOGY.md`** gained a TL;DR/abstract and a consolidated **Threats to
  validity** section (detectable-effect bound, positive control, static-vs-adaptive
  scope); the benchmark-quality report card is now a paper-style write-up.
- Recruiter-oriented phrasing neutralised to a neutral reference voice; rounded
  out `[project.urls]` (Homepage / Documentation / Changelog) for the PyPI sidebar.

### Security
- Validate `--pack-id` as a safe single path segment (reject `../` traversal and
  absolute paths) at both the library and CLI boundary.
- Documented that Hugging Face datasets are loaded **data-only** (no remote code;
  `datasets` ≥ 4 has no `trust_remote_code`).
- Pinned all third-party GitHub Actions to full commit SHAs (supply-chain
  hardening), notably for the OIDC-privileged publish workflow.

### CI
- Coverage is computed (`--cov=src/redteam`) and gated with `--cov-fail-under=75`
  so it can't silently regress.

## [0.2.1] — 2026-07-04

Maintenance release: corrects the package author/copyright metadata (the first
publish carried the wrong author), adds automated releases, and rounds out the
community-health files.

### Added
- **Automated PyPI releases via Trusted Publishing** (`.github/workflows/publish.yml`)
  — publishing a GitHub Release builds and uploads to PyPI over OIDC, with no
  stored token; the job also verifies the tag matches the package version.
- Community-health files: `SECURITY.md` (private reporting for vulnerabilities
  and suspected exclusion-filter leaks), `CODE_OF_CONDUCT.md` (Contributor
  Covenant 2.1), GitHub issue forms + a PR template.

### Changed
- Corrected the package **author / copyright** metadata to `Cheng-Yuan King`
  (`rosscyking1115@gmail.com`) in `pyproject.toml`, `LICENSE`, and the README
  citation. The public **contact** address (`rosscyking@gmail.com`) in the
  security / conduct / disclosure lines is unchanged.
- The benchmark-quality scorecard datasets are now **pinned to commit SHAs**
  (`scripts/hf_scorecard.py`), so `docs/findings/benchmark-quality-report-card.md`
  reproduces exactly.

## [0.2.0] — 2026-07-02 — the adversarial benchmark foundry

Repositioned from a static red-team harness (`llm-redteam-harness`) into an
upstream **benchmark foundry** (`redteam-foundry`). The v1 measurement core is
unchanged; these are additive. First public release.

### Added
- **Corpus quality audit** (`redteam corpora audit`) — exact + near-duplicate
  detection including cross-source overlap, composition, prompt-length stats,
  and label-integrity checks, rendered as a quality report + data card.
- **Language + attack-family taxonomy** — script-based language/code-switching
  detection and heuristic attack-family surface markers, surfaced in the audit.
- **Benchmark staleness scoring** (`redteam corpora staleness`) — a transparent,
  component-broken-out heuristic composing corpus and run signals.
- **Benign control set + defence comparison** (`redteam compare-defences`,
  `redteam benign export`) — false-refusal rate and
  `safe_usefulness = (1 - ASR) * (1 - FRR)` per defence config.
- **Multilingual over-refusal** (`redteam frr-by-language`,
  `redteam benign export --multilingual`) — benign control set in
  zh-Hant / zh-Hans / ja / ko + code-switched, with per-language FRR.
- **Challenge-pack exporter** (`redteam export-pack`) — versioned packs
  (`pack.yaml` + `scenarios.jsonl` + `datacard.md`) with adversarial prompts
  redacted by default, plus a reader (`redteam.packs.read_challenge_pack`) and
  a downstream consumption contract (`examples/export_to_agent_release_gates.md`).
- **Audit any Hugging Face dataset** (`redteam corpora audit-hf --dataset ...
  --prompt-column ... [--revision ...]`) — not just the four built-in corpora;
  the safety exclusion filter runs first. New `source="external"` /
  `category="unknown"` schema values back it.
- **Cross-dataset benchmark-quality scorecard** (`scripts/hf_scorecard.py`) and a
  written finding (`docs/findings/benchmark-quality-report-card.md`) auditing four
  public jailbreak datasets: all English-only, roleplay-persona-dominant, and
  duplicated to varying degrees.
- `docs/ROADMAP.md`; committed real-data findings under `reports/samples/`.

### Fixed
- Exclusion-filter leaks (WMD "synthesis" noun, several self-harm phrasings,
  case-insensitive category gate) with regression tests.
- Budget guard now **reserves** its estimate so concurrent calls can't
  collectively exceed the per-run cap.
- Llama Guard fails **closed** on an empty/errored verdict.
- Spotlighting / SecAlign neutralise their own fence markers in untrusted input
  (closes a delimiter-injection bypass); SecAlign no longer passes messages
  through unfenced.
- OpenAI target fails loud without a pricing entry (no silent $0 budget bypass).
- Krippendorff's α finite-sample correction; `compute_kappa` blank-cell guard;
  cross-judge agreement reports `None` (not `0.0`) when not computable.

### Changed
- **Renamed the project/package to `redteam-foundry`** (was
  `llm-redteam-harness`). The `redteam` CLI command and `src/redteam/` module are
  unchanged — `pip install redteam-foundry` still gives you `redteam ...`.
- Default install slimmed: the unused dashboard deps (`streamlit`, `plotly`)
  moved to an opt-in `[dashboard]` extra. The audit / staleness / dedup path
  needs no API key.

## [0.1.0] — v1 measurement core

- Loaders for AdvBench, JailbreakBench, HarmBench, AgentDojo (commit-pinned) with
  a safety exclusion filter.
- Anthropic + Ollama targets (OpenAI stub); disk response cache; per-run and
  per-call budget guards.
- Six composable defences (system prompt, Constitutional, Spotlighting,
  SecAlign, Llama Guard 4 pre/post).
- Rule-based + LLM-judge scoring with an independent cross-judge; bootstrap
  confidence intervals; Cohen's κ and Krippendorff's α.
- UK AISI Inspect eval-log export.

[0.2.1]: https://github.com/rosscyking1115/redteam-foundry/releases/tag/v0.2.1
[0.2.0]: https://github.com/rosscyking1115/redteam-foundry/releases/tag/v0.2.0
[0.1.0]: https://github.com/rosscyking1115/redteam-foundry/releases/tag/v0.1.0
