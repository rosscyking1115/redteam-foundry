# Inventory — have vs. new (Gate 1, resolved 2026-07-13)

The have-vs-new split that decides whether the paper is achievable. Resolved
against the actual repo (not `[VERIFY]` placeholders). **Verdict: 60/40 gate
PASSES** — the core exists at paper-grade; the MVP adds two bounded probes.

## Corpora (pinned — `configs/dataset_versions.yaml`)
| Corpus | Pin | Licence | In reported matrix? |
| --- | --- | --- | --- |
| AdvBench (llm-attacks) | `098262e` | MIT | Yes (direct) |
| JailbreakBench / JBB-Behaviors | `886acc3` | MIT | No (loadable) |
| HarmBench | `8e1604d` | MIT | No (loadable) |
| AgentDojo (ethz-spylab) | `18b501a` | **AGPL** | Yes (static indirect) |

**Release note:** MIT corpora → derived perturbed items + labels are releasable.
**AGPL (AgentDojo)** → confirm licence compatibility before releasing derived items.

## Models
| Model | Role | Status |
| --- | --- | --- |
| `claude-sonnet-4-6` | frontier target | HAVE (run) |
| `llama3.1:8b` (Q4) | local target | HAVE (run) |
| `llama2-uncensored:7b` | positive control | HAVE (run) |
| Qwen2.5-7B-Instruct, Mistral-7B-Instruct-v0.3, Gemma-2-9B-it | expand to publishable bar (≥3 families) | **NEW (to run)** |
| 1 frontier API (GPT-class) | closed+open span | NEW (optional, budget) |

Note: **Qwen2.5-7B is not yet run** (the source plans assumed it was aspirational).

## Existing results (paper-grade already)
- **Saturation:** 0–4% ASR across the 12-cell matrix; cross-judge **κ=+1.00 in all
  12 cells** (`METHODOLOGY.md` §8; regen via `scripts/headline_table.py --check`).
- **Positive control:** `llama2-uncensored:7b`, AdvBench n=100, no defences →
  judge ASR **80.0%** [72,87]; cross-judge **80.6%** [72.4,87.8], **κ=+0.935**
  (`METHODOLOGY.md` §12.5).
- **Detectable-effect bound:** n=100/0 successes → 95% CI [0, 3.6%].

## Infrastructure (reuse — do not rebuild)
- `src/redteam/orchestrator.py` — run / score / cross-judge pipeline.
- `src/redteam/stats.py` — `bootstrap_proportion_ci`, `bootstrap_mean_ci`,
  `krippendorff_alpha_binary` (seed=42 default; deterministic).
- `scripts/headline_table.py` — regenerate-and-`--check` discipline (extend paper-wide).
- `src/redteam/targets/` (registry + `OllamaTarget`), `src/redteam/scorers/judge_claude.py`
  (judge adapter pattern), `src/redteam/multilingual.py` (benign control set — NOT a
  perturbation tool).

## New work for the MVP
- **Probe A** — item-perturbation / verdict-flip generator (`src/redteam/perturb.py`);
  moderate, reuses the orchestrator. No variant support exists today.
- **Probe B** — human **gold-label set** (150–300 stratified) + published protocol +
  judge-vs-human analysis. No gold labels committed today; κ/α infra reusable.
- **Model/judge expansion** — configs for the new open-weight models; a third-family
  (non-Claude) judge adapter.

## Out of scope (upside; explicit reopen only)
Probe C contamination (`staleness.py` has no n-gram/pretraining-overlap logic →
major new capability); adaptive attacks (GCG/PAIR/TAP); live AgentDojo agent loop;
>6 models.
