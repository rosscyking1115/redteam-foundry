# Preregistration — does locale provenance change safety measurement?

**Status: design only. No models have been run. No outcomes have been collected.**

This document is written before any model call so that the analysis cannot be
chosen after seeing the numbers. Where a decision is still open it says so
rather than leaving the choice to be made later and presented as planned.

---

## 1. What this is not

Three claims that a reader might expect from a document with this title, and
which this project explicitly does not make.

**It is not a claim that flagship Taiwan benchmarks are converted Simplified
Chinese.** An earlier version of this hypothesis held that TMMLU+, TMLU and the
TCEval components were Simplified corpora pushed through OpenCC. That is wrong,
and the primary sources contradict it. TMMLU+ was built from 962 Taiwanese
examination papers (1998–2023), manually checked, and deliberately retains
Taiwan-specific content including Hokkien and Indigenous cultural material. Its
authors use OpenCC only for an *ablation* converting Taiwanese text **to**
Simplified, and they explicitly warn about the vocabulary problem, citing
內存 versus 記憶體. The hypothesis was tested and refuted, and the refutation is
recorded here because it is the reason this project exists in its current form.

**It is not the first Traditional Chinese safety benchmark, and not a claim that
non-English safety is understudied.** TS-Bench (Hsu et al., 2026) is a
Taiwan-native, human-curated safety benchmark with matched benign hard
negatives. The wider claim is refutable by XSafety, MultiJail, AnswerCarefully,
PolyGuard, LinguaSafe, ML-Bench&Guard, J-AISI's aisev, and CSSBench.

**It is not the first identification of Taiwan-native versus converted text.**
VarDial 2019 deliberately used OpenCC to build parallel script tracks and
classified Mainland versus Taiwan provenance, with a best Traditional-track
macro-F1 of 0.9084. SC-TC-Bench (FAccT 2025) formalises 110 regional term pairs
and 352 names. Regional Chinese variation is already operationalised, and a
novelty claim resting on it collapses immediately.

**The surviving claim, stated narrowly:**

> whether three or four semantically matched **provenance renderings** change
> **safety-classifier verdicts**.

Neither audit found that in the searched record. Everything else in this design
is prior art, and the writeup must say so.

**Japanese is out of scope.** AnswerCarefully already separates violation rate
from acceptable-response rate precisely because a model can score safe by
declining to answer. That finding is taken and is not re-derived here.

---

## 2. The question

> Does **locale provenance** change safety **measurement**, even when benchmark
> designers are trying to do the right thing?

Concretely: do glyph-only conversion, dictionary localisation, and native
Taiwan authorship of the **same semantic intent** produce different guard
classifier decisions, different LLM-judge verdicts, and different model
rankings?

The logic that makes this worth running:

> If the semantic content is identical and only the locale rendering differs,
> then any change in the safety verdict is a measurement artefact **by
> construction.**

This is the same shape as the repository's existing findings — the instrument
returning different answers to the same question — applied to locale rather
than to benchmark staleness.

---

## 3. Conditions

Four renderings per item, produced by `src/redteam/provenance.py`.

| | Condition | Construction | Role |
|---|---|---|---|
| **C** | native | Taiwan-authored, as published | **primary** |
| **A** | glyph-only | `C → tw2sp → s2t` | **primary** |
| **B** | dictionary-localised | `C → tw2sp → s2twp` | mechanism probe |
| **D** | Hong Kong | `C → tw2sp → s2hk` | mechanism probe |

**The primary contrast is A vs C.** B and D are mechanism probes, reported
separately rather than symmetrically. Treating all conditions as
interchangeable labels weakens the analysis and invites the objection that the
whole effect is a handful of `TWPhrases` lookups — §5 answers that with a
number instead.

**Arm D asks a different question.** `s2hk` = `STPhrases, STCharacters,
HKVariantsPhrases, HKVariants`. It loads no `HKPhrases` — only `s2hkp` does,
and that file holds 39 entries — so it introduces no Cantonese morphology: no
嘅, 咗 or 喺. Its output is mechanical Traditional standard Chinese under Hong
Kong glyph conventions, which is neither Taiwan text nor real Hong Kong
informal writing.

What it buys: whether a Taiwan-tuned guard is **Taiwan-specific** or merely
**Traditional-Chinese-general**. Verdicts that move identically for B and D
indicate the latter, and that is a finding either way. It costs nothing.

One result already recorded, because it inverts the naive expectation:
`HKVariants` maps 臺→台, and neither `TWVariants` nor `TWPhrases` does. So on
台灣 and 台女 — the study's highest-salience terms — **the Hong Kong rendering
reproduces the native form and both Taiwan renderings destroy it.**

**Why the round trip.** Running the transform backwards from Taiwan-native text
means all three renderings derive mechanically from one source, so semantic
intent is identical by construction and no human equivalence judgement is
needed to establish it. Running it forwards from a Simplified corpus would
require someone to author the native rendering, which is where the
single-annotator limit would bite hardest.

**Why `s2twp` and not `s2tw`.** Read from the installed configs:

```
s2t    = STPhrases, STCharacters
s2tw   = STPhrases, STCharacters, TWVariantsPhrases, TWVariants
s2twp  = STPhrases, STCharacters, TWPhrases, TWVariantsPhrases, TWVariants
```

`s2tw` runs a real Taiwan character-variant stage (裏→裡, 爲→為, 麪→麵). What it
lacks is `TWPhrases`, the word-level vocabulary dictionary. `s2twp` is the
dictionary condition because it is the only chain carrying vocabulary. `s2tw`
is retained as an unreported intermediate so the two stages can be attributed
separately (§5).

An earlier version of this document claimed `s2tw` "collapses into `s2t`". That
was false — generalised from five probes selected for vocabulary, which
therefore contained no variant characters that could have refuted it. Corrected
in `docs/findings/what-does-this-metric-return-when-nothing-happened.md` §8.

**`s2twp` is not comprehensive Taiwan localisation.** `TWPhrases` holds 775
entries against 4,800+ groups in Taiwan's official cross-strait difference list
(中華語文知識庫). Its proper-name coverage is sparse and uneven rather than
absent — 奧巴馬→歐巴馬, 新西蘭→紐西蘭, 老撾→寮國 are present; 布什→布希,
悉尼→雪梨, 里根→雷根 are not.

**Known limitation of the round trip.** Traditional→Simplified is many-to-one
(台/臺→台, 裡/裏→里, 吃/喫→吃, 才/纔→才, 為/爲→为). The return leg cannot recover
which source character was meant, so condition A carries *character-collapse*
artefacts in addition to *vocabulary* artefacts. A is therefore a superset of
the forward-direction effect, not a replica of it. The two are counted and
reported separately (`collapse_glyph_vs_native` versus `vocabulary_subs`); they
are never summed into one number, because they have different implications —
the dictionary route repairs vocabulary damage and cannot repair collapse.

---

## 4. Gate result (complete)

The gate asked whether the three renderings differ enough for an experiment to
exist. Run on the **complete TS-Bench corpus** — all 400 Taiwan-native items
(200 harmful, 200 matched benign hard negatives; 24,125 characters), pinned to
commit `b53fd7fabec6e053677cdfa68cdff4d7d1fba1b4`.

| Split | n | A vs B | A vs C | B vs C |
|---|---|---|---|---|
| All | 400 | **253 — 63.2%** | 264 — 66.0% | 154 — 38.5% |
| Harmful | 200 | 122 — 61.0% | 128 — 64.0% | 70 — 35.0% |
| Hard negatives | 200 | 131 — 65.5% | 136 — 68.0% | 84 — 42.0% |

Mean normalised edit distance A~B = 0.030. Substitutions split 381
character-variant / 275 vocabulary. Collapse artefacts: 205 against the
dictionary rendering, 313 against native.

**Kill criterion 1 does not fire.** The renderings are not the same text.

A 17-item pilot drawn from the paper's published example tables estimated the
A-vs-B rate at 65%, against 63.2% on the full corpus. Recorded because the pilot
was what authorised proceeding, and it is worth knowing it was not misleading.

Two observations that shape the analysis:

- **Both mechanical routes destroy `台女`** (Tai-Nu), the gendered slur TS-Bench
  singles out as culturally specific. It becomes `臺女` under A *and* under B,
  because 台/臺 is a collapse rather than a vocabulary substitution. `台灣`
  degrades the same way. **73 of 400 items** — 18% of the benchmark — carry a
  `台`→`臺` substitution that neither conversion route repairs.
- **Dictionary localisation drifts from native too**, in its own direction — it
  "corrects" the native author's 查看→檢視, 用戶→使用者, 點擊→點選. B differs from
  C on 38.5% of items. Neither mechanical condition recovers native text; they
  fail differently, which is why B is a condition in its own right rather than
  a corrected version of A.
- **Divergence is slightly higher on the benign hard negatives than on the
  harmful items** (65.5% vs 61.0%). Over-refusal is therefore not a secondary
  concern here: the control half of the benchmark is at least as exposed to
  rendering artefacts as the half being controlled.

What the gate does and does not establish: it shows the three conditions are
different *text*. Whether that changes a *verdict* is the study, and is not yet
measured.

---

## 5. Outcomes

### Primary

**Verdict-change rate between A and C**: the proportion of items whose binary
safety verdict differs between the native rendering and the glyph-only
rendering, on semantically identical content.

Because the same items appear in every condition, the comparison is paired.
Analysis is **McNemar's exact test** on the discordant pairs, reported with 95%
percentile-bootstrap confidence intervals over items, matching the interval
convention already used in this repository. **Cochran's Q** across all four
conditions is secondary.

### Every triplet is a bundle of measured edits

Recorded per prompt, so an effect can be attributed to a stage rather than to a
label. Implemented in `provenance.EditProfile`:

| Quantity | What it isolates |
|---|---|
| character-restoration edits | C → A: `STCharacters` / `STPhrases` |
| Taiwan-variant edits | A → `s2tw`: `TWVariants*` |
| `TWPhrases` edits | `s2tw` → B: word-level vocabulary |
| Hong Kong variant edits | A → D: `HKVariants*` |
| one-to-many opportunities | source chars with >1 traditional target (275 in the pinned inventory) |
| one-to-many gold correctness | did A restore the character the native author wrote? |
| token counts per rendering | the length/tokenisation confound |

The native text is the gold standard for one-to-many correctness, which is what
makes it machine-checkable without an annotator. Where a phrase rule changes a
span's length, per-position alignment is invalid and the item is counted as an
opportunity but **not** as scorable — `ambiguity_accuracy` returns `None` rather
than a flattering number.

### Secondary

1. Model ranking changes across conditions.
2. Guard false-negative and false-positive shifts, computed against the source
   benchmark's own labels, which the round trip preserves.
3. LLM-judge verdict shifts.
4. Over-refusal on the benign hard negatives, reported separately from the
   harmful items and never averaged with them.

### Smallest effect worth reporting

**5 percentage points** absolute in verdict-change rate, with a 95% confidence
interval excluding zero. Below that the result is reported as null regardless of
statistical significance. This number is fixed here, before any model has been
run.

### Absence rate

Every cell reports an explicit absence rate: blank, non-responsive, generic
disclaimer, truncated, and irrelevant responses, counted and published rather
than folded into a denominator. A guard that emits nothing must not be able to
score as agreement, and a judge that cannot parse a response must not be able to
score as a verdict. This is the house standard in
`docs/findings/what-does-this-metric-return-when-nothing-happened.md`, applied to
this project's own new metrics.

---

## 6. Semantic equivalence — who judged it

Equivalence between A, B and C is **established by construction**, not by
judgement: all three derive mechanically from one published source via recorded,
deterministic OpenCC configurations.

What remains a judgement is narrower: whether any individual round trip
*damaged* meaning badly enough that the item should be dropped as no longer
carrying the source intent. That audit is **single-author** — one reviewer,
a native Taiwan Mandarin speaker, with no second annotator and no adjudicator.

**Both commissioned audits state the same limit independently**: semantic
equivalence and localness judgements need **at least two independent native
Taiwan annotators**, and a single-idiolect native condition is itself a named
kill criterion. There is one annotator. That is disclosed here, in the findings
document, and in any writeup — not buried.

This bounds the work. It is portfolio-grade, not publication-grade. Concretely:

- Any claim resting on human labelling of **model outputs** is reported as a
  small disclosed sample and never as a primary outcome, because that genuinely
  requires two independent annotators plus adjudication.
- The primary outcome deliberately requires **no** human safety annotation. Guard
  verdicts, judge verdicts and model rankings are machine-measured end to end.
  The single-author limit therefore does not reach the headline.

---

## 7. Instruments and pinning

- **Guard classifier**: `MediaTek-Research/Breeze-Guard-26` (Apache-2.0, 8B,
  Taiwan-tuned, binary `<score>yes|no</score>`), revision `db4f493`. It is the
  sharpest available instrument because it was tuned on the TS-Bench
  distribution — a Taiwan-tuned guard returning different verdicts for
  glyph-only and native renderings of a prompt it was built to catch is the
  strongest single result reachable here.
- **Precision. Results are 4-bit only.** NF4, double-quantised, bf16 compute,
  at roughly 1.6 s per call.

  bf16 was attempted as an unquantised confirmation and **could not be run on
  the available hardware** — 16 GB of weights against an 8 GB card, with the
  CPU-offload path segfaulting and CPU-only inference at 229 s per call. The
  attempt and its outcome are recorded in `docs/bf16-confirmation-plan.md`,
  whose analysis plan was fixed before the attempt.

  **The quantisation caveat therefore stands and is disclosed rather than
  deleted.** Every number is a 4-bit number, the precision is recorded in the
  run header, and no claim here is an unquantised claim.

  Both require `transformers` 4.x. Version 5.14.1's weight-placement path
  segfaults on the development host under every `device_map`, including
  explicit single-device; 4.57.6 loads the same model on the same GPU without
  incident. The run therefore executes in a pinned, isolated environment.
- **Generators** (when Tier 2 runs) must include **at least one Taiwan-tuned
  model** — `Llama-3-Taiwan-8B`, and Breeze if it runs locally. A study about
  Taiwan locale sensitivity whose target set contains no Taiwan-tuned model is
  missing the models most likely to be sensitive to the manipulation. Pairing a
  Breeze generator with the Breeze guard is a natural condition rather than a
  confound **provided it is reported as such**, and it is.
- Every model is a dated version. System prompts, decoding, seed and run date
  are pinned and recorded, as elsewhere in this repository.

### Judges must not share a training lineage

Two Anthropic models are **not** two independent judges. Same lab, same
training lineage, correlated blind spots: if both misread Taiwanese register
the same way, the design cannot detect it, and their agreement would be
reported as validation.

The judge pair is therefore **cross-family**: one Western frontier model and
one Chinese-trained model (DeepSeek or Qwen-Max). Different training data is
what makes the second judge informative rather than confirmatory. Inter-judge
agreement is reported, and **disagreement is treated as data about the
instrument, not as noise to be averaged away** — the same posture this
repository already takes toward `refusal_rate`.

This costs no more than a same-family pair.

---

## 8. Kill criteria

Stated in advance. The project stops and reports a negative result if:

1. Renderings A and B barely differ on the chosen corpus. **Resolved: does not
   fire.** Recorded in §4. Note that this criterion strictly kills the
   *dictionary* condition only — A can still diverge from C when A and B agree,
   as it does for 台女. Both comparisons are reported.
2. Verdict changes between conditions fall under 5 points with intervals
   excluding a meaningful effect.
3. The only difference is that Taiwan readers prefer the wording. That is
   localisation QA, not safety-measurement validity.
4. Model rankings, guard errors and judge errors are stable across all three
   conditions.
5. The effect is explained by prompt length, tokenisation, or a change in actual
   harmfulness rather than by locale. Prompt length and token count are recorded
   per rendering so this can be tested rather than asserted.
6. It appears for one obsolete model or one weak classifier only.
7. Source-corpus licensing prevents releasing paired derivatives.
8. All tested models are at ceiling or floor.
9. A response-level Taiwan-native benchmark with paired localisation controls is
   released first. **Checked: does not fire.** TS-Bench is prompt-level and
   contains no paired localisation controls; OpenCC and script conversion do not
   appear in it.
10. **Most A/B/C/D triplets are byte-identical or differ only in 台/臺.** The
    corpus would then carry too few locale-bearing opportunities for the
    contrast to be about locale at all. Instrumented *before* the run as
    `GateReport.trivial_item_rate`, which separates fully-identical items from
    台/臺-only items rather than merging them.
11. **The effect disappears after controlling for token count, tokenisation,
    named entities and lexical edit count.** Token counts per rendering and
    per-stage edit counts are recorded per prompt (§5), so this is testable in
    the first analysis rather than as a later concession.
12. `s2tw` is treated as identical to `s2t`, or `s2twp` is described as
    comprehensive Taiwan localisation. Both are refuted by the configs, and
    both were asserted by an earlier version of this document. Pinned by
    `tests/unit/test_opencc_pin.py`.
13. OpenCC version and dictionary hashes are not frozen, so the treatment
    cannot be reproduced. **Resolved:** `src/redteam/opencc_pin.py` (§9a).

---

## 9. Source corpora and licensing

| Corpus | Licence | Redistribution of paired derivatives |
|---|---|---|
| TS-Bench (Hsu et al., 2026) | Apache-2.0, `github.com/mtkresearch/TS-Bench` | Permitted, with licence copy and notice of modifications |
| Safety-Prompts (thu-coai) | Apache-2.0 | Permitted, on the same terms |

**Kill criterion 7 is resolved.** The paper's scope note hedges on data
availability, so this was verified against the actual repository rather than the
paper: `data/TSB400.csv` is present and public under Apache-2.0, and the corpus
is pinned here at commit `b53fd7fabec6e053677cdfa68cdff4d7d1fba1b4`. The OpenCC
configuration recorded per item constitutes the required notice of modification.

No prompt text from any source corpus is committed to this repository — the
cache lives under the gitignored `/data/` tree, as for every other corpus here.

### 9a. The treatment is frozen by content, not by name

"OpenCC" alone is not a treatment definition. `src/redteam/opencc_pin.py`
records the package version (1.4.1), the upstream commit
(`81223ed87ae53283ef518e2deac34b7971f8a39e`, tag `ver.1.4.1`), and both the
source and compiled SHA-256 of every dictionary in every chain used.
`verify_pin()` fails loudly if an installed file drifts.

This is load-bearing, not bookkeeping. OpenCC master carries an **August 2026
fix to greedy `s2twp` matching** that is not in the pinned release, and several
dictionaries have gained entries since it: `TWPhrases` 775 → 817,
`TWVariants` 38 → 40, `TWVariantsPhrases` 4 → 12. A run reporting only
"converted with OpenCC" is not reproducible.

| Dictionary | Entries (pinned) |
|---|---:|
| STCharacters | 4,012 (275 with multiple targets) |
| STPhrases | 49,139 |
| TWPhrases | 775 |
| TWVariants | 38 |
| TWVariantsPhrases | 4 |
| HKVariants | 66 |
| HKVariantsPhrases | 272 |
| HKPhrases | 39 (not loaded by `s2hk`) |

Counts exclude each file's licence/provenance comment header; counting raw
lines inflates every figure by 6 to 16 and silently disagrees with the
published counts.

No prompt text from any source corpus is committed to this repository. The
provenance module transforms text supplied by the caller and reports metrics;
run artifacts remain gitignored, as elsewhere here.

---

## 10. Decisions taken

**10.1 — ETHICS.md scope: mechanical conversion only.** `ETHICS.md` now permits
deterministic script and locale conversion of *already-published* prompts, under
two stated conditions: the source must be published under a derivative-permitting
licence and pinned, and the exclusion filter must be able to read the target
script. Authoring novel harmful prompts in any language remains excluded, in
every language, and publishing rendered adversarial prompt text remains excluded.
The round-trip design was chosen partly to keep this amendment as small as
possible — nothing is authored, only transformed.

**10.2 — Corpus: TS-Bench, terms verified before fetch.** Verified against the
repository rather than the paper (§9), then pinned. The forward arm over
Safety-Prompts remains available as a robustness check on whether the effect
survives outside a round trip, and is not part of the preregistered primary
analysis.

**Still not decided, and deliberately so:** nothing about the run itself. No
model has been called, no verdict collected, no analysis performed. The
quantities in §5 are fixed before that happens, which is the point of this
document.

---

## 11. Prerequisite completed — the filter could not read Chinese

Independent of which arm runs, one defect had to be fixed first.

The exclusion filter is the mechanism behind this repository's central ethical
guarantee. Every one of its patterns was anchored on `\b` word boundaries and
ASCII letters. Chinese is unspaced and non-ASCII, so **no pattern could match any
Chinese prompt**. `filter_prompt` returned `excluded=False` for all Chinese
input — because it could not read it, not because the input was clean. A gate
that passes everything it cannot parse returns exactly the value of a gate with
nothing to catch.

This is a further instance of the pattern catalogued in
`docs/findings/what-does-this-metric-return-when-nothing-happened.md`, and it was
sitting inside the safety gate itself.

Fixed in `src/redteam/corpora/_filters.py`: a Chinese blocklist covering all
three excluded categories, matching Simplified and Traditional forms in the same
expression. It carries no optional dependency, deliberately — an OpenCC-based
normalising filter would silently degrade to the original blindness whenever the
extra was absent. `tests/unit/test_exclusion_filter.py` now asserts that the
English patterns alone cannot match the Chinese positive cases, that the full
filter catches them anyway, and that a Simplified and a Traditional writing of
one prompt receive the same verdict — so script conversion is not a route around
the gate.

---

## References

- Hsu, P.-C., Chen, M.-H., Chao, T. L., Han, C. T., & Shiu, D.-S. (2026).
  *Taiwan Safety Benchmark and Breeze Guard: Toward Trustworthy AI for Taiwanese
  Mandarin.* arXiv:2603.07286.
- *CSSBench: Evaluating the Safety of Lightweight LLMs against Chinese-Specific
  Adversarial Patterns.* arXiv:2601.00588.
- Safety-Prompts (thu-coai), Apache-2.0.
- Röttger et al. (2024), on hard negatives and over-refusal measurement.
