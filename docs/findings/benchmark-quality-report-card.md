# Are published jailbreak benchmarks still worth running?

*A reproducible measurement of whether the static adversarial corpora the field
still cites can discriminate 2026-era models — produced entirely by this repo's
own tooling. Every number below traces to a committed artifact under
[`reports/samples/`](../../reports/samples/) or regenerates with one command.*

**Author:** Cheng-Yuan King · **Updated:** 2026-07-06

---

## Abstract

Teams reach for published jailbreak corpora (AdvBench, HarmBench, JailbreakBench,
AgentDojo, and the many Hugging Face "jailbreak-prompt" datasets) as a safety
signal: *attacks succeed ~0% → we're fine.* We test whether those corpora still
**discriminate** modern models. Running commit-pinned corpora against a frontier
model (Claude Sonnet 4.6) and a small local model (Llama 3.1 8B) through
composable prompt-defence stacks — 12 evaluation cells, every verdict scored by
one LLM judge and re-scored by an independent second judge — we measure an
attack-success rate (ASR) of **0–4%**, with prompt-only defences producing no
measurable reduction, and **perfect inter-judge agreement on ASR (Cohen's
κ = +1.000 in all 12 cells)**. Auditing the corpora themselves shows why the
number is uninformative: the popular public datasets are **100% English**,
**dominated by persona/"DAN"-style role-play**, and **materially duplicated**.
The result is a **negative / meta-science finding about benchmark validity**: on
2026 instruction-tuned models these static corpora no longer separate a robust
model from a stale benchmark, and ASR alone cannot tell the two apart. The
contribution is the reproducible, judge-validated *measurement* of that
saturation, plus staleness and corpus-audit tooling to quantify it — not a new
attack, and explicitly not a robustness claim against an adaptive adversary.

## 1. Research question

> **RQ.** On 2026-era aligned models, do the static, published adversarial
> corpora the field relies on still *discriminate* — i.e., produce an attack
> signal that separates a robust model from a weak one — and how much can we
> trust whatever signal they give?

"Discriminate" is the operative word. A benchmark that scores every current model
at ~0% is not necessarily measuring safety; it may simply have saturated. The
question is answered in two halves: (a) an outcome measurement (ASR + its
validation), and (b) an audit of the corpora that produced it.

## 2. Method

**Targets.** Claude Sonnet 4.6 (frontier, Anthropic API) and Llama 3.1 8B Q4
(local, Ollama). **Corpora.** AdvBench (direct attacks) and AgentDojo (static
indirect injection), each pinned to an upstream commit; plus four public Hugging
Face jailbreak datasets for the corpus audit, pinned in
[`scripts/hf_scorecard.py`](../../scripts/hf_scorecard.py). **Defences.**
Composable prompt-layer stacks (paranoid system prompt, spotlighting, SecAlign-
style structured queries, constitutional critique-and-revise). **Scoring.** A
rule-based pre-screen (never a published number), then a primary LLM judge
(Claude Haiku 4.5), then an independent cross-judge (Claude Sonnet 4.6); ASR
carries a 95% percentile-bootstrap confidence interval. Full design, defence
definitions, and per-cell numbers are in
[`METHODOLOGY.md`](../../METHODOLOGY.md) (the source of truth for every figure
quoted here).

Everything below is either a committed artifact or regenerable:

```bash
python scripts/headline_table.py --check   # headline ASR table from cached runs (no API)
python scripts/hf_scorecard.py             # cross-dataset audit (network; no API key)
```

## 3. Results

### 3.1 The public jailbreak datasets are monolingual, meme-heavy, and duplicated

Auditing four public Hugging Face jailbreak datasets with `corpora audit-hf`
(first 300 rows each, post-safety-filter — full table in
[`reports/samples/hf_scorecard.md`](../../reports/samples/hf_scorecard.md)):

| dataset | exact-dup | near-dup pairs | languages | top attack family | staleness (corpus) |
| --- | ---: | ---: | --- | --- | ---: |
| rubend18/ChatGPT-Jailbreak-Prompts | 1.3% | 5 | English only | roleplay_persona (37/79) | 0.28 |
| jackhhao/jailbreak-classification | 0.0% | 8 | English only | roleplay_persona (58) | 0.10 |
| TrustAIRLab/in-the-wild-jailbreak-prompts | 3.3% | 28 | English only | roleplay_persona (84) | 0.24 |
| deadbits/vigil-jailbreak-ada-002 | 0.0% | 34 | English only | roleplay_persona (58) | 0.39 |

Three consistent facts: **100% English** (zero code-switching in any of them);
**persona/role-play jailbreaks dominate** every dataset (the "DAN" lineage); and
**duplication is real and uneven** (vigil packs 34 near-duplicate pairs into 104
prompts). A monoculture of dated memes is a poor instrument for measuring 2026
deployment risk.

### 3.2 On pinned corpora, attacks barely land — and defences can't discriminate

The 12-cell headline matrix (judge-scored, cross-validated; regenerate with
`python scripts/headline_table.py`):

| Benchmark | Target | Defence | ASR | 95% CI | cross-judge κ |
| --- | --- | --- | ---: | --- | ---: |
| AdvBench (direct, n=100) | Sonnet 4.6 | baseline / full-stack | 0% / 0% | [0,0] / [0,0] | +1.000 |
| AdvBench (direct, n=100) | Llama 3.1 8B | baseline / full-stack | 1% / 0% | [0,3] / [0,0] | +1.000 |
| AgentDojo (static indirect, n=50) | Sonnet 4.6 | baseline … full stack | 0% | [0,0] | +1.000 |
| AgentDojo (static indirect, n=50) | Llama 3.1 8B | baseline | 4% | [0,10] | +1.000 |
| AgentDojo (static indirect, n=50) | Llama 3.1 8B | +spotlighting / +SecAlign / full | 0% | [0,0] | +1.000 |

Scoring these runs for staleness
([`reports/samples/staleness/`](../../reports/samples/staleness/)):

| corpus | staleness | what drives it |
| --- | ---: | --- |
| AdvBench | 0.38 | max baseline ASR 1%; defences shift ASR ≤ 1pp |
| AgentDojo (static) | 0.43 | same near-universal failure + heavy templated duplication |

Both decompose the same way: the `universal_low_asr` and `low_defence_sensitivity`
components carry the score, while `judge_disagreement` is **0.00** — because
cross-judge κ = +1.000, the ASR metric itself is well-posed. The benchmark isn't
noisy; it has simply stopped discriminating.

### 3.3 The defences are "free" here — but also have nothing to defend

Running the benign control set through Sonnet 4.6, baseline vs the full
prompt-defence stack
([`reports/samples/defence_comparison_frr/`](../../reports/samples/defence_comparison_frr/)):

| config | ASR | false-refusal | safe-usefulness | cost | latency |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 0% | 0% | 1.00 | 0.14 | 3.1s |
| full stack | 0% | 0% | 1.00 | 0.41 | 4.6s |

The paranoid stack doesn't over-block legitimate requests (0% false refusal) —
but it also has nothing to defend (0% ASR) while costing ~3× and adding latency.
Across Traditional/Simplified Chinese, Japanese, Korean, and code-switched benign
prompts, false refusal is likewise **0%**: Sonnet 4.6 does not over-refuse
non-English input (which many models do).

## 4. Threats to validity

The headline is a null, so it is worth being explicit about how it could be wrong
or over-read. This mirrors, in brief, the consolidated section in
[`METHODOLOGY.md §12`](../../METHODOLOGY.md#12-threats-to-validity).

- **Detectable-effect floor.** At n=100/0 successes the 95% CI is **[0, 3.6%]**;
  at n=50, **[0, 7.1%]**. The design rules out ASR above roughly those rates, not
  a genuinely rare failure below them.
- **Positive control — passed.** A near-zero ASR could also mean the *harness*
  is under-eliciting. Ruled out empirically: run through the *same* pipeline, a
  known-vulnerable model (`llama2-uncensored:7b`, AdvBench n=100, no defences)
  scores **80% ASR** (cross-judge 80.6%, κ = +0.935 — METHODOLOGY §12.5). The
  apparatus registers a high ASR when the target is vulnerable, so the 0–4% is
  the aligned targets' property, not a measurement artifact.
- **Same-family judges.** Both judges are Claude-family. Perfect κ shows they are
  *consistent*, not that they are *externally calibrated*; a third-family judge
  or a human gold set would strengthen the claim at this ~0% base rate.
- **Static, not adaptive.** See §5 — this is a static-corpus measurement, not an
  adaptive-attack evaluation; 0–4% is a floor for that threat model only.
- **Static agent render = lower bound.** AgentDojo cells render each injection as
  a single prompt rather than running the live tool-use loop, which the upstream
  paper reports produces materially higher ASR.
- **Staleness is a heuristic**, deliberately component-broken-out — a flag for
  review, never a verdict; a low ASR is never proof a model is safe.

## 5. Related work — where this sits

This project measures **static, published** corpora and validates that
measurement. It is deliberately *not* an adaptive-attack evaluation, and it is
complementary to — not a competitor of — the following:

- **Adaptive / optimisation attacks** — GCG (gradient-based suffix search),
  PAIR (query-efficient iterative refinement), and TAP (tree-of-attacks search)
  *generate* new adversarial inputs against a target and routinely achieve far
  higher success than any fixed corpus. Our result says nothing about them; a
  motivated adversary using these methods is a different, harder threat model,
  and 0–4% on static prompts is a floor beneath it, not a ceiling over it.
- **Standardised red-team evaluation** — HarmBench provides a standardised
  harness and comparison across many attacks and models. This repo is narrower
  (a handful of corpora and prompt defences) but adds two things that harness-
  style leaderboards usually treat as given: an explicit **staleness/discrimination
  audit of the benchmark itself**, and **inter-judge agreement as a first-class,
  per-cell output** rather than a single trusted judge.
- **Agentic prompt injection** — AgentDojo defines the indirect-injection
  scenarios used here; we render them statically (an acknowledged lower bound)
  rather than running the full agent loop.
- **Evaluation infrastructure** — every run exports to a
  [UK AISI Inspect](https://inspect.aisi.org.uk/) eval log, so these measurements
  drop into the same tooling the wider eval ecosystem uses.

The gap this fills is a meta-science one: not "how well does attack X do," but
"**is this benchmark still a valid instrument, and how much do I trust the score
it produced.**"

## 6. Limitations

Beyond §4: two targets and four corpora is a small sample of the model and
benchmark space; defences are prompt-layer only (guard-model cells need larger
VRAM than the dev machine); attacks are single-turn and text-only; and the result
characterises *these* datasets with *these* defences, not a general "safety
score." The multilingual work is benign-only by policy (see
[`ETHICS.md`](../../ETHICS.md)).

## 7. Conclusion & future work

On 2026 instruction-tuned models, the popular static jailbreak and static
indirect-injection corpora no longer discriminate: they score robust and weak
configurations alike at ~0%, prompt-only defences can't move a number that is
already floored, and their monolingual / persona-meme / duplicated profile makes
them a weak instrument for real deployment risk. They remain useful for
refusal-boundary and regression testing — but should be reported *with* their
staleness, not as a bare "attacks succeed 0%." **Validate the benchmark before
you trust the gate.**

The under-elicitation objection is already closed: a positive control shows the
same pipeline reports **80% ASR** on a known-vulnerable model (§4). The
highest-value next steps, in order:

1. **Third-family or human-gold judge** — externally calibrate the ~0% base rate
   (both current judges are Claude-family), including on the positive-control cell.
2. **Live AgentDojo agent loop** — replace the static-render lower bound with the
   real multi-step tool-use measurement.
3. **Adaptive-attack track** (GCG/PAIR/TAP) — measure the threat model this study
   deliberately excludes.

## Reproduce

```bash
# Headline ASR table from cached runs, asserted against METHODOLOGY §8 (no API):
python scripts/headline_table.py --check

# Cross-dataset corpus scorecard (network; no API key):
python scripts/hf_scorecard.py

# One dataset, pinned:
redteam corpora audit-hf --dataset owner/name --prompt-column prompt --revision <sha>

# Staleness on a pinned corpus (needs cross-judged run JSONs):
redteam corpora staleness --only advbench --run results/<run>.cross-judged.json
```

See [`METHODOLOGY.md`](../../METHODOLOGY.md) for how each metric is validated and
its threats-to-validity section, and [`docs/ROADMAP.md`](../ROADMAP.md) for
what's next.
