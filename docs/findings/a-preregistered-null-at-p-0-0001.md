# A preregistered null at p = 0.0001

*What happens when statistical significance and a preregistered effect size
disagree, and the preregistration wins.*

**Author:** Cheng-Yuan King

---

## Summary

A Taiwan-tuned safety guard was shown 400 Taiwan-native safety prompts and three
mechanical conversions of each — the same semantic content, differing only in how
it had been rendered. The question was whether the rendering changes the guard's
verdict.

**It does, at p = 1.4 × 10⁻⁴. The result is reported as null.**

The preregistration fixed a minimum effect of 5 percentage points before any
model was run, and said in terms that anything below it is null "regardless of
statistical significance". The observed rate is 4.5%. That is the whole finding
and it is the reason this document exists: the interesting case for
preregistration is not when it confirms you, it is when it costs you a result
you can defend on every other axis.

Two substantive findings survive the null, and one prediction is refuted:

- **The pre-stated mechanism is wrong.** The effect was predicted to run through
  台→臺. A fourth rendering that *preserves* 台 is statistically
  indistinguishable from one that destroys it (1.8%, p = 1.0). 台 is a marker,
  not a cause.
- **The guard is sensitive to vocabulary, not to character variants.** The
  dictionary-localised rendering is indistinguishable from native (1.0%,
  p = 0.63); the two renderings lacking the vocabulary dictionary cluster
  together and apart from it.
- **Conversion is one-way.** When a verdict does change, it changes toward
  *more* restrictive, 17 times against 1.

---

## 1. The preregistered primary outcome

**Contrast:** native (C) versus glyph-only conversion (A), paired, McNemar's
exact test on discordant pairs, 95% percentile-bootstrap CI over items.

| | |
|---|---|
| Verdict-change rate | **18 / 400 = 4.5%** |
| 95% CI | [2.5, 6.8] |
| McNemar exact | b = 1, c = 17, **p = 1.449 × 10⁻⁴** |
| Preregistered minimum effect | **5.0 percentage points** |

The preregistration, quoted from the commit that predates the first guard call:

> **5 percentage points** absolute in verdict-change rate, with a 95% confidence
> interval excluding zero. Below that the result is reported as null regardless
> of statistical significance. This number is fixed here, before any model has
> been run.

4.5 < 5.0. **Null.**

The confidence interval excludes zero. The p-value is four orders of magnitude
below the conventional threshold. Neither is the criterion. A bar set after
seeing 4.5% would have been set at 4; the only defence against that is to set it
first and then honour it when it bites.

### Why this is the finding rather than a disappointment

Preregistration is usually described as protecting against false positives. This
is the other case, and it is the harder one: **a real, highly significant effect
that does not clear a threshold chosen in advance.** Everything about the result
is publishable except its size.

The alternative — reporting p = 0.0001 as a positive result and quietly not
mentioning the 5-point rule — would have been undetectable to a reader. That is
precisely why the rule has to bind.

---

## 2. What the guard is actually sensitive to

Share of items judged unsafe, by rendering:

| Rendering | Unsafe | vs native | p |
|---|---|---|---|
| **C** native | 48.0% | — | — |
| **B** dictionary-localised (`s2twp`) | 48.5% | 1.0% | 0.63 |
| **A** glyph-only (`s2t`) | 52.0% | 4.5% | 1.4 × 10⁻⁴ |
| **D** Hong Kong (`s2hk`) | 52.2% | 4.8% | 7.6 × 10⁻⁵ |

The four renderings fall into two groups, and the split is not where it was
predicted to be:

- **B is indistinguishable from native.** The rendering carrying the Taiwan
  vocabulary dictionary behaves like the text a Taiwanese author wrote.
- **A and D are indistinguishable from each other** (1.8%, p = 1.0) and both
  differ from native.

The variable that separates the groups is `TWPhrases`, the word-level
PRC→Taiwan vocabulary dictionary. A and D lack it; B and C have Taiwan
vocabulary. Character variants do not separate them.

---

## 3. The pre-stated mechanism is refuted

The predicted mechanism was the character pair 台/臺 — the character in 台灣
(*Taiwan*) and in the gendered slur 台女, which glyph-only conversion replaces on
82 of its 83 opportunities.

Arm D was added as a control for a different question and turned out to be the
instrument that refutes this one. `HKVariants` maps 臺→台; neither `TWVariants`
nor `TWPhrases` does. So **D preserves 台 exactly where A destroys it**, across
73 items.

If 台 drove the effect, A and D should diverge on those items. They do not:

| Contrast | Rate | p |
|---|---|---|
| A vs D, whole corpus | 1.8% | 1.0 |
| A vs D, on the 73 台-affected items | 2.7% | 0.5 |
| C vs D, on the 73 台-affected items | 11.0% | 0.0078 |

The two renderings that differ *precisely and only* on the predicted mechanism
produce the same verdicts. Meanwhile D — which gets 台 right — diverges from
native on those items just as much as A does.

> **台 is a marker for locale-dense content, not a cause of verdict change.**

**This subgroup analysis was not preregistered.** The preregistration contains no
台-subgroup verdict-change test and no comparator for one; it appears there only
in the description of the conditions and in a kill criterion about trivial items.
The analysis is **exploratory** and is reported as a refutation of a prediction
rather than as a positive result. That distinction matters here more than usual,
because an exploratory subgroup that *confirmed* the prediction would deserve far
less weight than one that kills it.

### Why the refutation is worth more than the primary would have been

Controlling for "Chinese locale" by converting characters is a standard move. If
the sensitivity lives in vocabulary rather than in orthography, then **anyone who
has normalised script and considered locale controlled has controlled for the
wrong variable.** That holds whether or not the effect size clears 5 points.

---

## 4. Direction, as a secondary observation

The 5-point rule governs **verdict-change rate**. It says nothing about
**direction conditional on a change**. These are different estimands, and the
second is not a substitute for the first.

Among the 18 discordant pairs: **b = 1, c = 17.** Seventeen items the guard
passed as safe in native form it flagged as unsafe after glyph-only conversion;
one went the other way. Under symmetric measurement error the expectation is
about 9 and 9.

Concentrated in the benign half — and this split **was** preregistered, as
secondary outcome 4, "over-refusal on the benign hard negatives, reported
separately from the harmful items and never averaged with them":

| Split | Rate | b | c | p |
|---|---|---|---|---|
| Benign hard negatives | 6.0% | 1 | 11 | 0.0063 |
| Harmful | 3.0% | 0 | 6 | 0.031 |

Eleven benign Taiwanese prompts — the controls, the items a guard is supposed to
let through — became "unsafe" purely by passing through a converter.

**The primary outcome remains null, and the direction does not rescue it.** A
one-way effect that fails a preregistered effect-size bar is still an effect that
fails the bar. Direction is reported because it is real and because a reader
deciding whether to convert their corpus needs it; it is not reported as a
finding that recovers the primary. The difference between an honest secondary and
a post-hoc rescue is entirely in whether the null is restated plainly, so: **the
primary is null.**

---

## 5. Convergence, and what a practitioner should do

Two independent methods, neither of them the primary outcome, agree:

| Method | Finding |
|---|---|
| Corpus analysis (no model) | `s2twp` reproduces the author's character on **97.1%** of one-to-many opportunities, excluding the one contested pair |
| Behavioural test (this study) | `s2twp` is **indistinguishable from native** to the guard — 1.0%, p = 0.63 |

A text measurement and a behavioural measurement, computed from different
artefacts, converge on the same conclusion about the same configuration. That is
worth more than either alone.

> **If you must convert, use `s2twp`. Glyph-only conversion introduces a
> measurable one-way bias toward over-refusal.**

This survives the null intact, because it rests on the mechanism and the corpus
work rather than on the effect size. The corpus finding is documented separately
in [what mechanical conversion does to Taiwan-native safety
text](./what-mechanical-conversion-does-to-taiwan-native-safety-text.md).

---

## 6. Limits

**The length association reaches the population claim, not the within-pair
claim.** A McNemar pair is one item under two renderings, so the two arms of a
pair are near-identical in length — measured, not assumed:

| | Within-pair token delta | Between-item length |
|---|---|---|
| Discordant (n = 18) | 1.33 tokens (max 3) | 163.2 |
| Concordant (n = 382) | 0.74 tokens (max 6) | 148.8 |

Within a pair the renderings differ by about one token in a hundred and fifty. A
verdict that flips between them cannot be flipping because of length. What *is*
associated with length is **which items are sensitive at all**: discordant items
are around 10% longer.

So the precise limit is: the claim "*Taiwanese locale content is affected*" may
be more accurately "*longer, more locale-dense content is affected*". The claim
"*when a verdict flips, the rendering is what changed*" is not reached by it.

**Edit count is treatment dose, not a confound.** Discordant items carry 5.00
character-restoration edits against 1.91 for concordant ones. A confound is a
rival explanation; edit count is the magnitude of the intervention itself, so
this reads as dose-response rather than as an alternative cause. Length and edit
count are correlated and cannot be separated at this sample size.

**Eighteen discordant pairs.** Every subgroup and confound statement rests on
them. Intervals are wide and are printed rather than glossed.

**No multiple-comparison plan was preregistered.** None is applied
retrospectively. Twenty contrasts are reported; only the primary and the
harmful/benign split have preregistered standing, and everything else — the 台
subgroup, the A-vs-D probe — is exploratory and labelled so in place.

**Single annotator.** Semantic-equivalence and localness judgements need at least
two independent native annotators. There is one. This is why the primary outcome
was chosen to require no human labelling at all: the four renderings derive
mechanically from one source, so their equivalence is established by construction
rather than by rating.

**One guard, one corpus, one precision.** The 4-bit run is complete;
**bf16 was measured at 18.5 s/call and was not executed.** No number in this
document is a bf16 result. One guard classifier is not the field.

**Instrument health.** 1,600 calls, **0 empty responses, 0 unparseable verdicts,
0 missing cells.** That 0.00% is reported only because the detector was fired
against injected fixtures first — a blank response increments the empty counter,
an unparseable one increments its own, and two mutually-silent conditions are
*excluded* from the paired test rather than scored as agreement. An absence rate
from a detector that has never fired is not evidence, and this project has
catalogued that failure often enough to owe the check.

---

## Reproducing

Every figure derives from a frozen treatment and a pinned corpus. The
conversion is pinned by dictionary **content** — package version, upstream
commit, and per-file SHA-256 — not by version string, and the run header
records `pin_verified: true`. Guard model, revision, decoding parameters and
precision are recorded in the same header.

The corpus-side figures need no model and no API key.
