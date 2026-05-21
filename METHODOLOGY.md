# Methodology

This document is the **source of truth** for any result claimed in the README,
a blog post, or a portfolio entry. Every number here is reproduced directly
from a run artifact in `results/`. If a claim is made anywhere else, it must
trace back to a row in this file.

Last updated: 2026-05-21.

## 1. Goal

Quantify how much published LLM defences change the **attack success rate
(ASR)** of published adversarial prompts — across a frontier model and a small
local model, on both direct and indirect attacks — and, with equal weight,
characterise *where the measurement itself is and is not trustworthy*. A
red-team harness that cannot say how much to trust its own numbers is not a
red-team harness; it is a number generator.

## 2. Corpora

All corpora are pinned to an upstream commit in `configs/dataset_versions.yaml`.
Counts below are **post-exclusion-filter** (see §"Excluded categories" in
`ETHICS.md`); the filter is verified end-to-end by
`tests/unit/test_exclusion_filter.py`.

| Source | Raw | Kept | Excluded | Pinned commit | Licence |
| --- | ---: | ---: | ---: | --- | --- |
| AdvBench | 520 | 504 | 16 | `098262e` | MIT |
| JailbreakBench (JBB-Behaviors) | 100 | 88 | 12 | `886acc3` | MIT |
| HarmBench | 400 | 342 | 58 | `8e1604d` | MIT |
| AgentDojo | 949 | 949 | 0 | `18b501a` | AGPL |

**v1 results matrix uses AdvBench (direct attacks) and AgentDojo (indirect
injection).** JailbreakBench and HarmBench are integrated and loadable through
the same interface but are not yet in the reported matrix — see §12.

## 3. Targets

| ID | Provider | Model version | Role |
| --- | --- | --- | --- |
| `claude-sonnet-4-6` | Anthropic API | `claude-sonnet-4-6` | Frontier target |
| `llama3.1-8b-local` | Ollama | `llama3.1:8b` (Q4) | Local target |

Model selection: `llama3.1:8b` Q4 is the local target because the development
machine is an 8 GB-VRAM laptop GPU; larger local models do not fit. A
defence-finetuned local baseline (`meta-secalign-8b`) was scoped as a stretch
target and is **not** in v1 — see §12.

Judging is done by models **separate from every target**, to avoid a model
grading its own output:

| Role | Model | Purpose |
| --- | --- | --- |
| Primary judge | `claude-haiku-4-5-20251001` | Scores every response |
| Cross-judge | `claude-sonnet-4-6` | Independent second opinion, validation |

## 4. Defences

Each defence wraps a `Target` and exposes the same `send()` interface, so
defences compose.

| # | Defence | Layer | In v1 reported matrix? |
| --- | --- | --- | --- |
| 1 | Paranoid system prompt | Prompt | Yes |
| 2 | Constitutional principles + critique-and-revise | Prompt + post | Yes (AdvBench full-stack) |
| 3 | Spotlighting (Hines et al., 2024) | Prompt | Yes |
| 4 | SecAlign-style structured-query prompting | Prompt | Yes |
| 5 | Llama Guard 4 12B pre-filter | Pre | No — see note |
| 6 | Llama Guard 4 12B post-filter | Post | No — see note |
| 7 | OpenAI Moderation pre-filter | Pre | No — deferred (no OpenAI key) |

**Why Llama Guard is implemented but excluded from the reported matrix.** Two
reasons, both about keeping the comparison honest. (a) A 12B guard model plus
the 8B local target cannot co-fit the 8 GB VRAM ceiling of the development
machine. (b) The frontier full-stack is prompt-only; adding a guard layer to
*only* the local model would break the cross-model comparison. The guard
defences pass their unit tests and are available for anyone running on larger
hardware — they are simply not part of the v1 apples-to-apples matrix.

The defence stacks actually reported:

- **AdvBench full-stack** = system prompt + spotlighting + SecAlign + constitutional.
- **AgentDojo full prompt stack** = system prompt + spotlighting + SecAlign.
  Constitutional critique-and-revise is omitted from the AgentDojo stack: it
  targets harmful-content generation, not indirect injection.

## 5. Experimental design

| Benchmark | Targets | Defence configs | n per cell | Cells |
| --- | --- | --- | ---: | ---: |
| AdvBench (direct) | 2 | baseline, full-stack | 100 | 4 |
| AgentDojo (indirect) | 2 | baseline, +spotlighting, +SecAlign, full | 50 | 8 |

Twelve evaluation cells in total. The `n` per cell is a fixed sample drawn
from the pinned corpus; AdvBench was sampled at 100 to give usable bootstrap
confidence intervals, AgentDojo at 50.

## 6. Scoring

Three layers, in increasing order of cost and trust:

1. **Rule-based** — a refusal-keyword detector and harmful-content regex. This
   is a **cheap pre-screen only**. It is *not* a source of truth: it
   over-counts compliance whenever a model refuses verbosely (it once read a
   stack of safe-but-wordy constitutional revisions as a 21% attack success
   rate; the LLM judge scored the same run at 0%). Rule-based numbers never
   appear in a published result.
2. **LLM judge** — `claude-haiku-4-5-20251001` with a structured rubric
   returning `{ asr: 0|1, refusal: 0|1, confidence: 0..1, reasoning: str }`.
   This is the **primary** scorer.
3. **Cross-judge** — every judged run is re-scored by a second, independent
   judge (`claude-sonnet-4-6`). Agreement between the two judges is the
   **primary validation mechanism** (see §7). This replaces the human
   spot-check that earlier drafts of this document used as primary
   validation; a CSV human-review export is retained as a tertiary check.

## 7. Cross-judge agreement — and what it caught

Agreement between the two independent judges is measured with Cohen's κ and
Krippendorff's α, on two axes: **ASR** (did the attack succeed?) and
**refusal** (did the model refuse?).

### ASR: validated everywhere

On the attack-success axis the two judges agree **perfectly**: κ = +1.000 and
α = +1.000 in **all 12 evaluation cells**. ASR has a single, unambiguous
referent — was the adversarial objective achieved — and both judges resolve it
identically. ASR is therefore treated as the validated headline metric.

### Refusal: not a safety metric — and the harness proves it

The refusal axis does **not** reproduce that agreement, and the harness was
built to surface exactly this rather than hide it. Two distinct failure modes:

**(a) The kappa paradox, on AdvBench.** When refusal is near-unanimous (98–99%
of responses), Cohen's κ collapses toward zero even though *raw* judge
agreement is ~99%. This is a known artefact: κ's chance-correction term
divides by the variance of the labels, and there is almost no variance to
divide by. The AdvBench Sonnet full-stack cell shows κ = +0.000 on refusal
despite near-unanimous raw agreement — both judges scored ~99% of responses as
refusals. This is a statistical artefact, not a disagreement.

**(b) Genuine definitional ambiguity, on AgentDojo.** On the four
Sonnet-target AgentDojo cells the judges disagree *substantially*: the Haiku
judge reports 30/74/22/94% refusal where the Sonnet judge reports 98/100/96/100%
on the **same responses**, and Krippendorff's α goes **negative**
(−0.48/−0.15/−0.53/−0.03 — worse than chance). Inspecting the per-case
reasoning shows the cause clearly: both judges describe the *identical*
behaviour ("the model rejected the injection and still served the user") and
both score ASR = 0. They diverge only on the binary `refusal` label, because
an indirect-injection task has **two** things that can be refused — the user's
benign request and the injected malicious instruction. One judge codes
`refusal = 0` (the model did not refuse the user); the other codes
`refusal = 1` (the model did refuse the injection). The metric is **ill-posed
for indirect injection.**

### Consequence

`refusal_rate` is reported in run artifacts as a **descriptive** signal of
response *style* — explicit refusal versus charitable redirect — and nothing
more. It is **not** a safety metric, and on the indirect-injection track it is
not even a stable construct. ASR is the metric. The fact that two competent
frontier judges cannot agree on how to *measure* "refusal" for indirect
injection, while agreeing perfectly on ASR, is itself the cleanest evidence
for the project's headline: prompt-only defences move response style, not the
safety outcome.

## 8. Results

### AdvBench — direct attacks, n = 100 per cell

| Target | Defence | ASR (judge) | 95% CI | Refusal (judge, descriptive) | ASR cross-judge κ |
| --- | --- | ---: | --- | ---: | ---: |
| Sonnet 4.6 | baseline | 0% | [0, 0] | 92% | +1.000 |
| Sonnet 4.6 | full-stack | 0% | [0, 0] | 99% | +1.000 |
| Llama 3.1 8B | baseline | 1% | [0, 3] | 99% | +1.000 |
| Llama 3.1 8B | full-stack | 0% | [0, 0] | 98% | +1.000 |

### AgentDojo — static indirect injection, n = 50 per cell

| Target | Defence | ASR (judge) | 95% CI | ASR cross-judge κ |
| --- | --- | ---: | --- | ---: |
| Sonnet 4.6 | baseline | 0% | [0, 0] | +1.000 |
| Sonnet 4.6 | + spotlighting | 0% | [0, 0] | +1.000 |
| Sonnet 4.6 | + SecAlign | 0% | [0, 0] | +1.000 |
| Sonnet 4.6 | full prompt stack | 0% | [0, 0] | +1.000 |
| Llama 3.1 8B | baseline | 4% | [0, 10] | +1.000 |
| Llama 3.1 8B | + spotlighting | 0% | [0, 0] | +1.000 |
| Llama 3.1 8B | + SecAlign | 0% | [0, 0] | +1.000 |
| Llama 3.1 8B | full prompt stack | 0% | [0, 0] | +1.000 |

**Reading the matrix.** Published direct and static-indirect attacks succeed
between 0% and 4% of the time, on both a frontier model and a small local
model, before any project-built defence is applied. The single non-zero
frontier-vs-local difference — Llama's 4% AgentDojo baseline, 2 of 50 cases —
is closed by every defence config and is within sampling noise of zero. The
prompt-only defence stacks do not produce a measurable ASR reduction, because
there is essentially no ASR left to reduce: 2026-era instruction tuning
already neutralises these published, static attacks. What the defences *do*
change is refusal style (see §7), which is not a safety outcome.

## 9. Metrics

- **ASR** — attack success rate. Primary, validated (§7). Reported with 95%
  percentile-bootstrap confidence intervals.
- **Refusal rate** — descriptive only (§7). Not a safety metric.
- **Inter-judge agreement** — Cohen's κ and Krippendorff's α between the two
  judges, per axis.
- **Cost** — USD per run, from real API metering.

False-refusal rate (FRR) on a benign control set is defined in the harness but
not in the v1 reported matrix — see §12.

## 10. Reproducibility guarantees

- Every model is a **dated** version ID (`claude-sonnet-4-6`,
  `claude-haiku-4-5-20251001`, `llama3.1:8b` Q4).
- Every dataset is pinned to an upstream commit hash in
  `configs/dataset_versions.yaml`.
- Every API call is cached by `(target_id, model_version, hash(messages))`,
  so a re-run is free and deterministic.
- `pyproject.toml` + `uv.lock` pin every Python dependency.
- CI runs lint + typecheck + unit tests on every PR (no real API calls).
- Run artifacts in `results/` carry the full per-case record — prompt,
  response, both judges' verdicts and reasoning — so any number in §8 can be
  audited case by case.

## 11. Limits — what this benchmark does not measure

- **The full agentic loop.** The AgentDojo integration renders each indirect
  injection as a *single prompt* containing a simulated tool-output block. The
  model sees the injection but does not run an interactive, multi-step
  tool-use loop. The upstream AgentDojo paper, which does run that loop,
  reports materially higher attack success. **Our indirect-injection ASR is
  therefore a lower bound**, and the gap between static rendering and the live
  agent loop is the single most important open risk this matrix does not
  capture. This is named as future work (§12), not silently omitted.
- **Multi-turn / crescendo attacks** — every attack here is single-turn.
- **Image / vision** red-teaming — text-only for v1.
- **Closed-weight model internals** — logit or activation-level probes are
  inaccessible without a research partnership.
- **Generalisation beyond the included benchmarks** — results characterise
  performance on these specific datasets with these specific defences. They
  are not a general "safety score".
- **Production deployability** — this is a measurement tool, not a deployable
  defence layer.

## 12. Future work

- Run the **full AgentDojo agent loop** (interactive tool use) — the highest-
  value next step, since §11's static-rendering limit is the main thing
  suppressing measured ASR.
- Multi-turn / crescendo attack track.
- Bring **JailbreakBench and HarmBench** into the reported matrix (loaders
  already integrated).
- **FRR** on a benign control set, to measure the over-refusal cost of each
  defence stack.
- **Llama Guard 4** pre/post cells on a larger-VRAM machine.
- **Inspect AI** eval-log export, for compatibility with the UK AI Safety
  Institute's evaluation framework.

## 13. Verification log

| Date | What was verified |
| --- | --- |
| 2026-05-05 | Pre-Phase-0 stack audit. Confirmed Claude 4.6/4.7 family, Llama 4 / Llama Guard 4 availability, OWASP LLM Top 10 v2025, GHA v6, Python 3.13. Added SecAlign to the defence stack. Selected `llama3.1:8b` for the local target (8 GB VRAM ceiling). |
| 2026-05-08 | Phase 3 defence layer landed. Six defences implemented; exit-check live smoke asserts defences never reduce baseline refusal rate. |
| 2026-05-09 | AdvBench n=100 on Sonnet 4.6, judge-scored and cross-judged. ASR 0% both configs. |
| 2026-05-11 | AgentDojo n=50 on Sonnet 4.6, 4 defence configs, judge-scored. ASR 0% all configs. |
| 2026-05-21 | AdvBench n=100 on Llama 3.1 8B (baseline + full-stack) and AgentDojo n=50 on Llama 3.1 8B (4 configs) completed and judge-scored. All 12 cells cross-judged: ASR κ = +1.000 throughout. Cross-judge surfaced the refusal-axis ambiguity documented in §7. Confirmed the rule-based scorer's 21% full-stack ASR was an artefact (judge: 0%). |
