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
`[llm-redteam-harness] takedown request`.

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

Ross — rosscyking@gmail.com
