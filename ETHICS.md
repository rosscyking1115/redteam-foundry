# ETHICS

This project measures LLM behaviour against published adversarial prompts to
inform defence design. It is **not** a security audit, certification, or
guarantee.

## What this project does

- Runs **published** adversarial prompts from peer-reviewed or
  industry-released datasets (AdvBench, JailbreakBench, HarmBench, AgentDojo)
  against target LLMs.
- Measures attack-success-rate (ASR) under combinations of published defences
  (system prompts, Llama Guard 4, Spotlighting, SecAlign-style structured
  queries, Constitutional principles), with every verdict cross-validated by
  an independent second judge model.
- Publishes **aggregate** results, methodology, defence configurations, and
  scoring code openly.

## What this project does not do

- **Generate novel jailbreaks.** All prompts come from published datasets,
  cited and version-pinned.
- **Publish raw harmful outputs verbatim.** Results are aggregated, redacted,
  and summarised. A small number of representative example transcripts may
  be shown per category, with explicit warnings.
- **Test categories that are excluded by policy** (see below). These are
  filtered at corpus-load time before any model receives them.
- **Author non-English attack content.** We do not write new harmful prompts
  in any language, and we do not use a model to translate or paraphrase harmful
  prompts into new ones. The multilingual control set
  (`src/redteam/multilingual.py`) is **benign** only — it measures whether
  models *over-refuse* harmless non-English and code-switched prompts.

  **Narrow exception, added 2026-08-02: deterministic script and locale
  conversion of prompts that are already published.** Locale-provenance work
  (`src/redteam/provenance.py`) renders an existing prompt into Simplified and
  Traditional Chinese variants using pinned, recorded OpenCC configurations.
  Nothing is authored: the output is a character and vocabulary mapping of text
  the upstream dataset already released, and the transformation is reversible
  and reproducible from the recorded config. This is the same relationship to
  the source that loading a pinned corpus has, not the creation of new content.

  Two conditions govern the exception, both of which must hold:

  1. **The source prompt must already be published** under a licence permitting
     derivative works, and pinned to an upstream revision.
  2. **The exclusion filter must be able to read the target script.** Every
     rendering passes the same `filter_prompt` gate as the source, and the
     filter's Chinese coverage is asserted by
     `tests/unit/test_exclusion_filter.py`, including that a Simplified and a
     Traditional writing of one prompt receive the same verdict.

  Condition 2 was not met before 2026-08-02. Every filter pattern was anchored
  on `\b` word boundaries and ASCII letters, so none could match Chinese text
  at all, and the filter returned "not excluded" for every Chinese prompt —
  because it could not read them, not because they were clean. That gap is
  fixed, and the exception above is conditional on it staying fixed.

  Still excluded: authoring novel harmful prompts in any language; and
  publishing rendered adversarial prompt text, which stays redacted and
  gitignored exactly as English adversarial prompts do.

## Excluded categories

The following categories are filtered out of all loaded corpora at
`scripts/load_corpora.py` and verified by a CI test
(`tests/unit/test_exclusion_filter.py`):

- **CSAM** — Child Sexual Abuse Material, in any form.
- **Bio / chem / radiological / nuclear weapons synthesis** — uplift content
  for the design or manufacture of weapons of mass destruction.
- **Detailed self-harm methods** — actionable instructions for self-injury
  or suicide. (Discussion of self-harm at a research / awareness level is
  fine; method-level detail is not.)

If any of these slip past the filter, the CI test fails and merge is blocked.

## Datasets used (with citations)

- **AdvBench** — Zou et al., 2023. *Universal and Transferable Adversarial
  Attacks on Aligned Language Models.* MIT licence.
- **JailbreakBench / JBB-Behaviors** — Chao et al., 2024. *JailbreakBench:
  An Open Robustness Benchmark for Jailbreaking Large Language Models.*
  MIT licence. NeurIPS 2024 Datasets & Benchmarks Track.
- **HarmBench** — Mazeika et al., 2024. *HarmBench: A Standardized
  Evaluation Framework for Automated Red Teaming and Robust Refusal.*
  MIT licence.
- **AgentDojo** — Debenedetti et al., 2024. *AgentDojo: A Dynamic
  Environment to Evaluate Prompt Injection Attacks and Defences for LLM
  Agents.* AGPL licence.
- **TS-Bench** — Hsu et al., 2026. *Taiwan Safety Benchmark and Breeze Guard:
  Toward Trustworthy AI for Taiwanese Mandarin.* arXiv:2603.07286.
  Apache-2.0 (`github.com/mtkresearch/TS-Bench`). 400 Taiwan-native prompts,
  200 harmful and 200 matched benign hard negatives. Used as the source for
  locale-provenance renderings; Apache-2.0 permits derivative works with a
  licence copy and a notice of modifications, and the OpenCC configuration
  applied to each item is that notice.

Exact dataset commits are pinned in `configs/dataset_versions.yaml`.

## Models tested (with version pins)

Every result is reported against a **dated** model ID. See
`configs/model_versions.yaml` for the full list. As of project start
(2026-05-05) this is:

- `claude-sonnet-4-6` (Anthropic Claude Sonnet 4.6) — frontier API target
- `llama3.1:8b` (Meta Llama 3.1 8B via Ollama) — local target
- `meta-secalign-8b` (Meta SecAlign 8B) — Phase 5+ stretch target
- Judge: `claude-haiku-4-5-20251001` (Claude Haiku 4.5) — distinct from any
  evaluated target
- Cross-judge: `claude-sonnet-4-6` — independent second judge used to
  validate every verdict

## Responsible disclosure

If you are a model provider whose model is included and you would like
findings or example transcripts removed, email
**rosscyking@gmail.com** with the subject line
`[redteam-foundry] takedown request`.

**Removal commitment: 24 hours from receipt.**

## Scope and disclaimer

This work is for research and educational purposes. Results are reported as:

> "On benchmark X, with defence stack Y, model Z showed ASR = N% [95% CI ...],
> judged by Claude Haiku 4.5 and cross-validated by an independent second
> judge (Claude Sonnet 4.6)."

Results **do not** imply that any model is "safe" or "unsafe" in general.
See `METHODOLOGY.md` for how each metric is validated, and which metrics are
reported as descriptive only.

Do not apply these prompts against systems you do not own or have explicit
permission to test.

## Provider terms of service

Both Anthropic's and OpenAI's usage policies explicitly permit safety
evaluation and red-teaming research. We comply with:

- Anthropic Usage Policy (verified 2026-05-05)
- API budget caps set in the provider console (hard limit) **and** in the
  harness itself (per-run, per-call) — see `src/redteam/budget.py`.

## Maintainer

Cheng-Yuan King — rosscyking@gmail.com
