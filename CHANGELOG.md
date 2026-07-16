# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
