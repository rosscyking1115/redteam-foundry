# Gate 0 — Kill-condition lit search & decision

**Date:** 2026-07-13 · **Decision: PARTIAL → proceed, re-led** (rule from the plan:
OPEN → paper · PARTIAL → paper re-led on the unoccupied angle, cite/differentiate ·
OCCUPIED → downgrade to repo+blog+Zenodo and stop).

This gate precedes any new experiment. It tests whether the *exact combination* this
paper claims is already published — not the individual axes (all of which are).

## What the question is
Has anyone published a **single, open, reproducible audit** that unifies **item-level
perturbation verdict-flips + judge-attributable score uncertainty on the SAME
saturated static safety benchmarks (AdvBench / AgentDojo) with aligned 2026 target
models**, led by **"benchmark saturation is invisible to ASR" (κ≈+1.00 on a metric
that no longer discriminates)** and anchored by a **positive control** that proves the
near-zero is the model's property, not harness under-elicitation?

## Method
Queries (July 2026) over arXiv cs.CL/cs.CR/cs.LG on: benchmark-saturation +
judge-agreement + validity audit; unified perturbation + judge-reliability +
open reproducible harness on AdvBench/AgentDojo; verdict-flip under
meaning-preserving rewrite; positive-control / under-elicitation. Reference lists of
the closest hits followed. **A final formal re-run is required at writing time**
(§ writeup) — the field is moving monthly.

## Nearest neighbours (cite + differentiate in Related Work)
| Paper | What it does | Overlap | Our delta |
| --- | --- | --- | --- |
| Judge Reliability Harness — 2603.05399 | Open library generating judge-reliability tests; 4 benchmarks incl. safety | The "open harness for judge reliability" axis (our Probe B, partially) | We add item-perturbation flips + saturation framing + positive control on target models; judge reliability is one component, not the claim |
| Policy Invariance — 2605.06161 | Verdict-flip ≤9.1% under content-preserving **policy** rewrites; released code | Flip-under-rewrite + open code | We perturb **benchmark items vs target models**, not the judge's policy text; tie flips to saturation |
| Judge-Config Sensitivity — 2604.24074 | 6 target models; judge-prompt wording shifts harmful-rate ≤24.2pp on HarmBench | Judge-side sensitivity; 6-model scale | We perturb the **item**, not the judge prompt; lead with saturation + positive control |
| Reliability without Validity — 2606.19544 | 21 judges/9 providers; κ-deflation, ranking instability | Judge (un)reliability at scale | Component only; our subject is benchmark validity on saturated aligned models |
| A Coin Flip for Safety — 2603.06594 | LLM judges fail to reliably measure adversarial robustness | Judge unreliability | Component only |
| Claw-Eval — 2604.06132 | Trajectory audit for autonomous agents; Completion/Safety/Robustness; open | "Unified open audit" framing | Different subject (agent trajectories), not static-benchmark item saturation/perturbation |
| Taxonomy of Safety Benchmarks for AI Agents — 2605.16282 | Taxonomy + consistency analysis | Benchmark consistency | Descriptive taxonomy, not a per-item validity audit with a positive control |
| EvalSafetyGap — 2606.30219 | Survey/framework of eval-safety failures | Framing | Survey, not measurement |

## Verdict & consequence
**PARTIAL.** The axes and even open judge-reliability harnesses exist, so the
"we built an open validity-audit harness" framing is **partly occupied** and must NOT
be the headline. The genuinely unoccupied angle — **re-lead on these:**
1. **Saturation invisible to ASR** — perfect two-judge agreement (κ≈+1.00) on a metric
   that no longer discriminates aligned 2026 models; the audit exposes what the
   standard metric hides. (No neighbour leads with this.)
2. **Positive control as method** — the same pipeline reports 80% ASR (κ=+0.935) on a
   known-vulnerable model, ruling out under-elicitation. (Not seen in the neighbours.)
3. **Item-perturbation tied to saturation** — "the little ASR that moves, moves on
   wording, not safety," distinct from judge-policy-rewrite (2605.06161) and
   judge-prompt-config (2604.24074) work.
4. **East-Asian over-refusal with native round-trip-translation QC.**

**Do NOT stop.** Do NOT frame the contribution as "an open harness for eval validity"
(occupied). Frame it as the saturation-invisible-to-ASR finding + positive control +
released labels, with the harness as supporting reproducibility infrastructure.

## To re-run at writing time (final gate)
Formal search for the exact combination against then-current arXiv/AF; if by then a
paper leads with saturation-invisible-to-ASR + positive control on these benchmarks →
re-assess OCCUPIED and consider the downgrade path.
