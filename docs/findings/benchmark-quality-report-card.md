# Are published jailbreak benchmarks still worth running?

A short, reproducible look at the *quality* of the adversarial benchmarks the
field relies on — produced entirely by this repo's own tools. Every number
below traces to a committed artifact under
[`reports/samples/`](../../reports/samples/) or is regenerable with one command.

> **TL;DR.** On 2026-era models, popular published jailbreak prompts barely
> succeed and the defences meant to stop them can't be told apart — because
> there's almost nothing left to stop. Meanwhile the benchmarks themselves are
> monolingual (English), lean heavily on dated "DAN"-style persona memes, and
> carry real duplication. A near-zero attack-success rate is at least as much a
> statement about the *benchmark* as about the *model*. Validate the benchmark
> before you trust the gate.

## Why this matters

Teams reach for AdvBench / HarmBench / jailbreak corpora as a safety signal:
"attacks succeed 0% → we're fine." But 0% is ambiguous — it can mean a robust
model *or* a benchmark that no longer measures real risk. Nobody ships a way to
tell those apart. This is that tool.

## 1. Public jailbreak datasets are monolingual, meme-heavy, and duplicated

Auditing four public Hugging Face jailbreak datasets with `corpora audit-hf`
(first 300 rows each, post-safety-filter — full table in
[`reports/samples/hf_scorecard.md`](../../reports/samples/hf_scorecard.md)):

| dataset | exact-dup | near-dup pairs | languages | top attack family | staleness (corpus) |
| --- | ---: | ---: | --- | --- | ---: |
| rubend18/ChatGPT-Jailbreak-Prompts | 1.3% | 5 | English only | roleplay_persona (37/79) | 0.28 |
| jackhhao/jailbreak-classification | 0.0% | 8 | English only | roleplay_persona (58) | 0.10 |
| TrustAIRLab/in-the-wild-jailbreak-prompts | 3.3% | 28 | English only | roleplay_persona (84) | 0.24 |
| deadbits/vigil-jailbreak-ada-002 | 0.0% | 34 | English only | roleplay_persona (58) | 0.39 |

Three consistent facts: **100% English** (0 code-switching in any of them);
**persona/role-play jailbreaks dominate** every dataset (the "DAN" lineage); and
**duplication is real and uneven** (vigil packs 34 near-duplicate pairs into 104
prompts). The safety filter also dropped a row from the in-the-wild set in
passing.

## 2. On pinned corpora, the attacks barely land — and defences can't discriminate

Auditing the repo's four commit-pinned corpora and scoring staleness against
real cross-judged runs
([`reports/samples/staleness/`](../../reports/samples/staleness/)):

| corpus | staleness | what drives it |
| --- | ---: | --- |
| AdvBench | 0.38 | max baseline ASR 1%; defences shift ASR ≤ 1pp |
| AgentDojo (static) | 0.43 | same near-universal failure + heavy templated duplication |

Both decompose the same way: `universal_low_asr` and `low_defence_sensitivity`
carry the score, while `judge_disagreement` is 0.00 — cross-judge Cohen's
κ = +1.000, so the attack-success metric itself is well-posed. The benchmark
isn't noisy; it's just no longer discriminating.

## 3. The defences are "free" here — but also useless

Running the benign control set through Claude Sonnet 4.6, baseline vs the full
prompt-defence stack
([`reports/samples/defence_comparison_frr/`](../../reports/samples/defence_comparison_frr/)):

| config | ASR | false-refusal | safe-usefulness | cost | latency |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 0% | 0% | 1.00 | 0.14 | 3.1s |
| full stack | 0% | 0% | 1.00 | 0.41 | 4.6s |

The paranoid stack doesn't over-block legitimate requests (0% false refusal) —
but it also has nothing to defend (0% ASR), while costing ~3× and adding
latency. And across Traditional/Simplified Chinese, Japanese, Korean, and
code-switched benign prompts, false refusal is **0%** — Sonnet 4.6 does not
over-refuse non-English input, which many models do.

## Takeaway

These published, static jailbreak benchmarks are still useful for
refusal-boundary and regression testing, but on 2026 instruction-tuned models
they no longer strongly measure real deployment risk, and their duplication /
monolingual / persona-meme profile should be known before they're used as
evidence. The open risk they *under*-measure is the live agentic loop
(multi-step tool use), which these static renderings don't exercise.

## Caveats (read these)

- **Staleness is a heuristic**, deliberately component-broken-out — not a verdict.
  A high score flags a benchmark for review; a low ASR is never proof a model is
  safe.
- The scorecard datasets are **pinned** to specific commits (in
  `scripts/hf_scorecard.py`), so the table reproduces exactly.
- Judges are one model family (Haiku + Sonnet); a third-family judge would
  strengthen the agreement claim.
- Sample sizes are modest; intervals are reported where it matters.

## Reproduce

```bash
# The cross-dataset scorecard (network; no API key):
python scripts/hf_scorecard.py

# One dataset, pinned:
redteam corpora audit-hf --dataset owner/name --prompt-column prompt --revision <sha>

# Staleness on a pinned corpus (needs cross-judged run JSONs):
redteam corpora staleness --only advbench --run results/<run>.cross-judged.json
```

See [`METHODOLOGY.md`](../../METHODOLOGY.md) for how each metric is validated and
[`docs/ROADMAP.md`](../ROADMAP.md) for what's next.
