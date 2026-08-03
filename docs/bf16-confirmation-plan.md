# bf16 confirmation run — analysis plan, fixed before results

**Written before the bf16 run completed.** The 4-bit run is already reported;
this document exists so that what will be claimed about the comparison cannot be
chosen after seeing it.

## Why run it at all

The 4-bit result is a **null on the preregistered primary**. A null is exactly
where "your instrument was degraded" bites hardest — a reader can dismiss a
non-effect by pointing at quantisation, and that objection costs nothing to make
and everything to answer afterwards. Removing the caveat is worth more for a null
than it would be for a positive result.

The run is local and free. Nothing is rented and nothing is spent.

## What is held constant

Identical corpus (pinned commit), identical four renderings, identical OpenCC
pin, identical prompt template, identical greedy decoding, identical parsing.
The **only** difference is precision:

| | 4-bit (reported) | bf16 (this run) |
|---|---|---|
| Weights | NF4, double-quantised, bf16 compute | bfloat16, unquantised |
| Per call | ~1.6 s | ~18.5 s |

## What will be reported, in each case

Stated now so neither outcome can be presented as the expected one.

**If the two precisions agree** — the primary verdict-change rate stays below the
preregistered 5-point bar, and the A/D versus B/C grouping is preserved:

> Report that the null is not an artefact of quantisation. Delete the
> quantisation caveat from the write-up rather than merely disclosing it. State
> the agreement quantitatively (per-condition base rates, primary rate, and the
> per-item verdict agreement between precisions), not as "consistent".

**If the two precisions disagree** — the primary crosses the 5-point bar in
either direction, or the grouping changes:

> **This is a finding, not a problem.** It would mean quantisation changes the
> safety behaviour of a guard classifier, which is a result this repository
> exists to produce: guards are commonly deployed quantised, and a guard whose
> verdicts move with its precision is a measurement instrument that reports its
> own compression. Report it as the headline of a separate finding, report both
> precisions side by side, and do **not** silently prefer the bf16 numbers as
> "the real ones" — neither is more real, they are two deployments.

**In both cases**, report per-item agreement between the two runs (the share of
the 1,600 calls receiving the same verdict at both precisions), because that is
the quantity that distinguishes "same conclusion" from "same verdicts".

## What does not change either way

- The **preregistered 5-point bar is not moved**. If bf16 lands at 4.9% that is
  still null; if it lands at 5.1% that clears the bar on the bf16 arm and the
  4-bit arm remains null. Both are reported, neither is chosen.
- **Tier 2 remains NO-GO.** The gate is on the 4-bit primary already reported,
  and a confirmation run is not a second attempt at the gate.
- The absence rate is reported with the fixture result beside it, as before. The
  detector has been fired against injected blank and unparseable responses; the
  rate is only evidence because of that.

## Sample-size note

The comparison is between two complete runs over the same 400 items, so it is
paired at the item level and does not inherit the n = 18 discordant-pair
limitation that constrains the 4-bit subgroup statements. Statements about
*within-4-bit* subgroups remain limited by that n regardless of what bf16 shows.
