# What mechanical conversion does to Taiwan-native safety text

*A reproducible corpus measurement. Every figure re-derives from a frozen
treatment and a version-pinned corpus; nothing here requires an API key or a
GPU.*

**Author:** Cheng-Yuan King · **Written:** 2026-08-02

---

## Summary

Safety benchmarks written in Traditional Chinese reach evaluation by different
routes. Some are authored natively in Taiwan. Some are converted from Simplified
Chinese with a character-mapping tool. The conversion is usually treated as a
formatting step.

It is not. Measured against 400 Taiwan-native safety prompts, converting them
down to Simplified and back with the standard tool:

- changes the text on **66% of items**;
- restores the **wrong character** on about **17% of one-to-many opportunities**
  (315 errors across 27 distinct character pairs);
- mangles **台** — the character in 台灣 *(Taiwan)* and in the gendered slur
  台女 — on **82 of its 83 opportunities**.

Turning on the tool's Taiwan-localisation option (`s2twp`) helps a lot: errors
fall from 315 to 131. But **79 of those 131 remaining errors are the single
substitution 台→臺**, and the option separately *introduces* errors by
"correcting" 聯繫→聯絡 and 數據→資料 where the Taiwanese author had written the
first form.

The sharpest single result is an accident of dictionary contents: **the Hong Kong
conversion preserves 台; both Taiwan conversions destroy it.**

**What this document does not establish:** whether any of this changes a safety
classifier's verdict. That measurement is designed and preregistered but not yet
run. Everything below is about the text.

---

## 1. What was measured

**Corpus.** TS-Bench (Hsu et al., 2026), the Taiwan Safety Benchmark: 400
human-curated single-turn prompts in Taiwanese Mandarin, evenly split into 200
harmful and 200 matched benign "hard negatives" — benign queries that resemble
harmful ones. Apache-2.0, pinned at commit `b53fd7f`.

Its content is culturally specific by design: Shopee phishing formats, 投顧老師
("investment teacher") pump-and-dump scripts, the shrimp-and-lemon-juice arsenic
rumour, the slur 台女, political epithets like 塔綠班. That specificity is what
makes it a useful probe — these are exactly the terms a generic converter has no
reason to protect.

**Treatment.** Each native prompt is pushed down to Simplified Chinese and
brought back up three ways, using OpenCC:

| | Rendering | Chain |
|---|---|---|
| **C** | native | as published |
| **A** | glyph-only | `C → tw2sp → s2t` |
| **B** | dictionary-localised | `C → tw2sp → s2twp` |
| **D** | Hong Kong | `C → tw2sp → s2hk` |

All four carry identical semantic intent by construction, because all derive
mechanically from one source. **C is the gold standard**: it is what the
Taiwanese curators actually wrote, so "did the converter pick the right
character?" is machine-checkable without a human annotator.

---

## 2. What the configurations actually do

Read from the installed config files, not from documentation:

```
s2t    = STPhrases, STCharacters
s2tw   = STPhrases, STCharacters, TWVariantsPhrases, TWVariants
s2twp  = STPhrases, STCharacters, TWPhrases, TWVariantsPhrases, TWVariants
s2hk   = STPhrases, STCharacters, HKVariantsPhrases, HKVariants
s2hkp  = STPhrases, STCharacters, HKPhrases, HKVariantsPhrases, HKVariants
```

Three things follow that are easy to get wrong, and one of which this project
did get wrong and published before catching it:

**`s2tw` is not a no-op over `s2t`.** It runs a real Taiwan character-variant
stage: 裏面→裡面, 爲了→為了, 麪條→麵條. What it lacks is `TWPhrases`, the
word-level vocabulary dictionary. An earlier version of this work claimed `s2tw`
"collapses into `s2t`", generalising from five probes that had been *selected*
to be vocabulary-bearing and therefore contained no variant characters capable
of refuting it. The correction is written up separately as a methodological
finding.

**`s2twp` is a partial vocabulary mapping, not comprehensive localisation.**
`TWPhrases` holds **775** entries. Taiwan's official cross-strait difference list
(中華語文知識庫) holds more than **4,800** groups. Its proper-name coverage is
sparse and uneven rather than absent — 奧巴馬→歐巴馬, 新西蘭→紐西蘭, 老撾→寮國
are present; 布什→布希, 悉尼→雪梨, 里根→雷根 are not.

**`s2hk` introduces no Cantonese.** It loads no `HKPhrases` (only `s2hkp` does,
and that file holds 39 entries), so nothing in it produces 嘅, 咗 or 喺. Its
output is mechanical Traditional standard Chinese under Hong Kong glyph
conventions — neither Taiwan text nor real Hong Kong informal writing. That makes
it a clean control for "is this tuning Taiwan-specific, or just
Traditional-Chinese-general?"

---

## 3. Result: the conversion changes most of the corpus

| Comparison | Items differing (of 400) |
|---|---|
| **A vs C** — glyph-only vs native | **264 — 66.0%** |
| B vs C — dictionary vs native | 154 — 38.5% |
| D vs C — Hong Kong vs native | 245 — 61.3% |
| A vs B | 253 — 63.2% |
| A vs D | 217 — 54.3% |

Split by half: **64.0%** on harmful items, **68.0%** on the benign hard
negatives. The controls are affected slightly *more* than the material they
control for, which matters for anyone using this kind of corpus to measure
over-refusal.

**A check against the obvious objection.** If most items were identical or
differed in one trivial way, the comparison would not be about locale at all.
Measured before drawing any conclusion: **102 items (25.5%) are fully identical
across all four renderings, and 14 more (3.5%) differ only by 台/臺** — 29.0%
trivial in total. The remaining 71% carry substantive differences.

---

## 4. Result: one restoration in six is wrong

Simplification merged historically distinct characters, so converting back is a
word-sense disambiguation problem, not a lookup. The pinned `STCharacters`
dictionary contains **275** source characters with more than one traditional
target. Each occurrence in a source text is an *opportunity* to pick the wrong
one.

Scored against the native gold, per position, over the whole corpus:

| Route | Correct | Wrong |
|---|---|---:|
| **A** `s2t` glyph-only | 1,555 / 1,870 — **83.2%** | 315 |
| **B** `s2twp` dictionary | 1,639 / 1,770 — **92.6%** | 131 |
| **D** `s2hk` Hong Kong | 1,693 / 1,870 — **90.5%** | 177 |

The Taiwan vocabulary dictionary earns its place: it cuts errors by well over
half. The denominators differ because `s2twp` fires more phrase rules, and where
a phrase rule changes a span's length, per-position alignment is invalid — those
opportunities are counted but **not** scored, and the accuracy figure reports
`None` rather than a flattering number.

The glyph-only errors are not evenly spread. The twelve most frequent:

| Native (gold) | Glyph-only produces | Count | What it breaks |
|---|---|---:|---|
| 台 | 臺 | **82** | 台灣 *(Taiwan)*, 台女 *(slur)* |
| 入 | 錄 | 59 | 登入 → 登錄 *(log in)* |
| 料 | 據 | 35 | 資料 → 數據 *(data)* |
| 裡 | 裏 | 24 | 這裡 → 這裏 *(here)* |
| 核 | 覈 | 20 | 核對 → 覈對 *(verify)* |
| 吃 | 喫 | 19 | 吃 → 喫, archaic |
| 才 | 纔 | 18 | 才 → 纔, archaic |
| 連 | 鏈 | 11 | 連結 → 鏈接 *(link)* |
| 盡 | 儘 | 8 | |
| 絡 | 繫 | 7 | 聯絡 → 聯繫 *(contact)* |
| 煙 | 菸 | 4 | |
| 了 | 瞭 | 4 | |

Two things stand out. Several are **exactly the Taiwan/PRC lexical splits** a
Taiwan-facing tool should protect — 登入/登錄, 資料/數據, 連結/鏈接, 聯絡/聯繫.
And several are **archaic forms no contemporary writer uses**: 喫 for 吃, 纔 for
才. The converted text is not merely PRC-flavoured; in places it is antique.

`s2twp` repairs all four of those lexical splits. What it does not repair is
§5.

---

## 5. Result: the Taiwan option leaves one character, and it is the worst one

Of the **131** errors `s2twp` still makes, **79 are the single substitution
台→臺** — 60% of its entire residual error budget on one character. Under
glyph-only conversion, `台` is restored wrongly on **82 of its 83 opportunities**.

```
native      台灣        台女
s2t         臺灣        臺女
s2tw        臺灣        臺女     ← Taiwan variants: no change
s2twp       臺灣        臺女     ← Taiwan vocabulary: no change
s2hk        台灣        台女     ← Hong Kong: correct
```

**`HKVariants` maps 臺→台. Neither `TWVariants` nor `TWPhrases` does.** So on the
two most Taiwan-specific tokens in the corpus, the *Hong Kong* conversion
reproduces what the Taiwanese author wrote and both *Taiwan* conversions destroy
it.

This is not a bug in OpenCC. 臺 is the prescriptive standard form and 台 the
overwhelmingly common one in actual Taiwanese usage; the Taiwan chains encode the
prescriptive preference, and the Hong Kong chain happens to encode the common
one. But the practical consequence for anyone building an evaluation corpus is
blunt: **the Taiwan localisation option leaves the single most Taiwan-specific
character wrong in 60% of its remaining errors, and the Hong Kong option
incidentally gets it right.**

### The dictionary also over-corrects

`s2twp` does not only fail to fix things — it introduces errors of its own, by
applying Taiwan vocabulary where the native author did not use it:

| Native wrote | `s2twp` produces | Count |
|---|---|---:|
| 聯**繫** | 聯**絡** | 9 |
| 數**據** | 資**料** | 5 |
| 儘 | 盡 *(reversed)* | 7 |

These are real Taiwanese authors writing 聯繫 and 數據 — forms the dictionary
treats as Mainland and "corrects" away. It is a reminder that `TWPhrases` encodes
a prescriptive mapping, not a description of how Taiwanese people write, and that
a localisation pass moves text toward a *standard* rather than toward the
*source*.

---

## 6. Where the changes come from

Reporting one undifferentiated diff invites the objection that the whole effect
is a handful of dictionary lookups. Attributing each conversion stage separately
answers it:

| Stage | Edits (whole corpus) |
|---|---:|
| Character restoration (`STCharacters`/`STPhrases`) | **820** |
| `TWPhrases` word-level vocabulary | **642** |
| Taiwan variants (`TWVariants*`) | **222** |
| Hong Kong variants (`HKVariants*`) | 411 |

Character restoration contributes more than the vocabulary dictionary does, so
the effect is **not** reducible to TWPhrases lookups. The 222 Taiwan-variant
edits are also the empirical refutation of the "`s2tw` collapses into `s2t`"
claim mentioned in §2 — that number would be zero if it were true.

---

## 7. Reproducing this

**"Converted with OpenCC" is not a reproducible treatment.** OpenCC's
dictionaries change between releases. The version used here is pinned by
content, not by name:

- package `OpenCC` **1.4.1**, upstream `BYVoid/OpenCC` commit
  **`81223ed87ae53283ef518e2deac34b7971f8a39e`** (tag `ver.1.4.1`)
- SHA-256 recorded for every dictionary, in both source and compiled form
- a verification function that fails loudly if an installed file drifts

| Dictionary | Entries |
|---|---:|
| STCharacters | 4,012 *(275 with multiple targets)* |
| STPhrases | 49,139 |
| TWPhrases | 775 |
| TWVariants | 38 |
| TWVariantsPhrases | 4 |
| HKVariants | 66 |
| HKVariantsPhrases | 272 |
| HKPhrases | 39 *(not loaded by `s2hk`)* |

This matters concretely: OpenCC master carries an **August 2026 fix to greedy
`s2twp` matching** that is not in the pinned release, and several dictionaries
have gained entries since it — `TWPhrases` 775→817, `TWVariantsPhrases` 4→12.
Results obtained on master will not match these.

> **A trap for anyone reproducing the counts.** Every dictionary file carries a
> licence and provenance comment header of **6 to 16 lines**. Counting with
> `grep -c .` or `wc -l` inflates *every* published figure — TWPhrases reads as
> 781 rather than 775, TWVariantsPhrases as 20 rather than 4. Exclude comment
> lines. All six counts above reproduce exactly once you do.

---

## 8. What this does and does not support

**Supported by the measurement above:**

- Mechanical conversion changes most Taiwan-native safety text.
- Glyph-only conversion restores the wrong character on roughly one opportunity
  in six, concentrating on Taiwan-specific vocabulary and on archaic forms.
- The Taiwan-localisation configuration cuts that error rate by more than half,
  but 60% of what it still gets wrong is one character, 台 — which the Hong Kong
  configuration incidentally gets right.
- That configuration also over-corrects, changing 聯繫 and 數據 as written by
  Taiwanese authors into 聯絡 and 資料.
- Any of these is reproducible offline from the pins in §7.

**Not supported, and not claimed:**

- **That any of this changes a safety verdict.** That is the question worth
  asking and it is not answered here. The experiment is preregistered — primary
  outcome, effect threshold, and kill criteria all fixed in advance — and the
  guard-classifier run has not produced results at the time of writing. If it
  comes back null, that null is the finding.
- **That this is the first work on regional Chinese variation.** It is not.
  VarDial 2019 already used OpenCC to build parallel script tracks and classified
  Mainland versus Taiwan provenance (best Traditional-track macro-F1 0.9084), and
  SC-TC-Bench (FAccT 2025) formalises 110 regional term pairs and 352 names.
- **That converted text is "wrong Chinese".** It is standard Traditional Chinese.
  The claim is narrower and only about measurement: text that reaches an
  evaluation by a different route is different text, and a benchmark that treats
  the route as invisible is not measuring what it reports.

### Limitations, stated plainly

**One annotator.** Semantic-equivalence and naturalness judgements about Chinese
text require at least two independent native annotators plus adjudication. This
work has one. Two commissioned audits state this independently, and it is why
the results above were chosen to be **machine-checkable against a published
gold standard** rather than to rest on judgement: "did the converter reproduce
what the Taiwanese curators wrote?" needs no rater. Any claim here that *would*
need raters — that condition C reads as more natural, that the errors matter to
a reader — is not made.

**One converter, one corpus, one release.** Every figure is conditional on
OpenCC 1.4.1 and on TS-Bench. A different converter or a corpus with different
vocabulary density would give different numbers. The pins in §7 exist so that
someone can check rather than assume.

**Round-trip artefacts.** Pushing native text down to Simplified and back is a
superset of the forward direction: Traditional→Simplified is many-to-one, so the
downward leg destroys distinctions the upward leg must guess at. That is
precisely the effect being measured, but it means these figures bound *round-trip*
degradation, and a corpus authored in Simplified and converted once would show
the vocabulary errors without some of the character-collapse errors.

---

## References

- Hsu, P.-C., Chen, M.-H., Chao, T. L., Han, C. T., & Shiu, D.-S. (2026).
  *Taiwan Safety Benchmark and Breeze Guard: Toward Trustworthy AI for Taiwanese
  Mandarin.* arXiv:2603.07286.
- OpenCC, `BYVoid/OpenCC`, tag `ver.1.4.1`.
- 中華語文知識庫 / 中華語文大辭典 cross-strait difference list.
- VarDial 2019 shared task, Chinese dialect identification.
- SC-TC-Bench (FAccT 2025), regional term and name pairs.
