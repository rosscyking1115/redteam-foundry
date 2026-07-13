# Pre-registered analysis plan (locked 2026-07-13, BEFORE any new run)

The interpretation rules are fixed **before** running the probes, so the result
cannot be read as fished-for. The git commit that adds this file is the timestamp;
it is not edited after runs begin except via a dated **amendment** section at the
bottom (append-only — never silently rewrite a pre-registered rule).

## Honesty invariants (overriding — from the plan §0)
- **INV-1** Negative / meta-science result about *benchmark validity*; no claim any
  model is safe/unsafe, no new attack.
- **INV-2** Every claim backed by a repo number; no adjective does a number's job.
- **INV-3** Limitations written as a hostile reviewer would.
- **INV-4** Every figure regenerable from a pinned script (`--check` discipline).

## Hypotheses (falsifiable, per probe)
- **H-A (Probe A):** on saturated aligned models, benchmark verdicts that *do* change
  under meaning-preserving perturbation change on **wording**, not the safety
  property → a non-trivial per-item verdict-flip rate under perturbation.
- **H-B (Probe B):** a non-trivial share of a benchmark's score is attributable to
  **judge idiosyncrasy** rather than the underlying property → judge-vs-human and
  cross-judge disagreement above a pre-set bound, with the prevalence caveat stated.
- **H-sat (existing):** static ASR has saturated (0–4%) yet κ≈+1.00 — perfect
  agreement on a metric that no longer **discriminates** (saturation invisible to ASR).

## Metrics & estimators (fixed)
- **Primary Probe-A metric:** per-item **verdict-flip rate** = fraction of items whose
  judged binary verdict (ASR label, and separately the refusal label) changes between
  the original item and its perturbed variant, per (perturbation type × benchmark ×
  model). Judge = primary judge; confirmed on the cross-judge.
- **Primary Probe-B metric:** **judge-attributable score uncertainty** per benchmark =
  (a) Cohen's κ(primary judge, human) and κ(judge1, judge2, judge3 pairwise);
  (b) the swing in measured benchmark score (ASR / refusal rate) across the judge set.
- **Uncertainty:** 95% **percentile-bootstrap** CIs on *every* headline number
  (`stats.py`, 10,000 resamples, seed=42). Agreement: **Cohen's κ** for 2 raters;
  **Krippendorff's α** for ≥3 raters, both with bootstrap CIs.
- **Base rates reported beside every κ/α** (the benchmarks are near-all-refusal;
  κ is prevalence-sensitive — this is load-bearing for H-sat, not hidden).

## Pre-stated interpretation thresholds (set now)
- **Baseline jitter** = verdict-flip rate under a **no-op / trivial-reformat** control
  perturbation (whitespace only). All flip rates are read *relative to* this.
- **Probe A — "verdict tracks wording":** a (type × benchmark × model) cell is flagged
  if its flip-rate 95% CI **lower bound exceeds baseline jitter by ≥ 5 percentage
  points**. Report all cells with CIs regardless; flagging is descriptive, not a gate.
- **Probe B — "judge-attributable uncertainty is material":** flagged if κ(judge,human)
  point estimate **< 0.60** (below Landis–Koch "substantial") **or** the score swing
  across the judge set **≥ 5 percentage points**, with base rates reported. κ cut-offs
  (Landis–Koch) are reported but not over-leaned-on (prevalence caveat).
- **H-sat framing rule:** report κ **with** the label base rate every time; never
  present κ≈+1.00 as "the benchmark is reliable" — it is "agreement on a
  non-discriminating metric."

## Multiple-comparison discipline (fixed)
- Probe A comparison count = (#perturbation types) × (#benchmarks) × (#models),
  enumerated in the results table. Apply **Benjamini–Hochberg** FDR control at
  **q = 0.05** across the Probe-A family; report both raw and BH-adjusted.
- State the exact number of comparisons run in the paper (a hostile reviewer counts).

## Controls retained
- **Positive control** (`llama2-uncensored`, 80% ASR, κ=+0.935) stays prominent — the
  answer to "did you just fail to elicit?".
- **Detectable-effect bounds** (n=100/0 → [0, 3.6%]) retained to pre-empt
  absence-of-evidence-vs-evidence-of-absence.

## Scope fence (fixed — MVP)
IN: Probe A + Probe B on the core matrix (4–6 models across ≥3 families + third-family
judge) + existing saturation/positive-control formalised. OUT (upside, explicit
reopen): Probe C contamination; adaptive attacks; live AgentDojo loop; >6 models.

## Sampling & compute (fixed intent)
Perturbation runs use a **sampled subset** of items per benchmark (not the full
corpus) to fit the A100 allocation; the sample size per cell is recorded in the
results table and its CIs reflect it. Judging cost is small (~$0.1–0.3 per cell,
per the positive-control run).

---
## Amendments (append-only; dated; never rewrite the above)
*(none yet)*
