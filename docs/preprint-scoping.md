# Scoping: what it would take to get a submittable arXiv preprint

Status: **scoping only — no writing started.** Written 2026-07-27.
Decision owner: Ross.

Companion to [`inspect-evals-port-scoping.md`](./inspect-evals-port-scoping.md),
which established that an arXiv URL is a hard prerequisite for an
`inspect_evals` register listing, and that the sequence is paper → port →
register. This document assesses the paper honestly: what exists, what is
missing, and how long.

**Headline: the writing is the smaller half.** The report card is closer to a
paper than most repo write-ups ever get. The two things that actually gate
submission are an *endorser* (a person, not a task) and a *related-work section
that currently does not exist in any form*. My round-1 estimate of "days, not
hours" was right in magnitude but missed the endorsement problem entirely.

---

## 1. Two hard gates, verified from primary sources

### 1.1 The arXiv URL requirement has no alternative

`register/README.md`, verbatim:

> "**arXiv URL** — the paper your eval implements (prefer a versioned URL, e.g.
> `/abs/1234.5678v1`)."

> "Why is an arXiv URL required? The bot uses the arXiv paper to automatically
> derive eval metadata..."

It is described as "a quality control requirement that ensures that the
methodology behind the eval's design and implementation is publicly available."
No alternative venue is named — not OpenReview, not ACL Anthology, not a tech
report or personal site. The only escape hatch mentioned is contacting a
maintainer directly for control over `eval.yaml` fields, which is not an
exemption from the field itself.

So: no arXiv paper, no listing. This is a genuine dependency, not a nice-to-have.

### 1.2 arXiv endorsement changed on 21 January 2026 — and a Sheffield email is no longer enough

This is the finding that reshapes the estimate. As of 2026-01-21, across all
categories:

> "arXiv will no longer accept institutional email addresses...as the sole
> qualifier of endorsement for new authors."

Institutional email is now necessary but **not sufficient**. A first-time
submitter to a category has two paths:

| Path | Requirement | Ross's status |
| --- | --- | --- |
| 1 | Institutional email **and** "previous authorship on an existing paper which has been accepted to the arXiv 'endorsement domain' they wish to submit to" | ❌ institutional email yes, prior authorship in-domain no |
| 2 | "seeking personal endorsement directly from an established arXiv author in the same endorsement domain" | the only available route |

Endorsers must have authored a qualifying number of papers in that endorsement
domain, counting only papers "submitted between three months and five years
ago."

**Consequence: the critical path runs through a person.** No amount of writing
quality shortens it, and it can be started today, in parallel with everything
else. It should be.

### 1.3 A corollary worth acting on: cs.CR may be the wrong primary category

Endorsement is per *endorsement domain*. The obvious endorser candidates in
Ross's orbit are NLP/ML people — a Sheffield supervisor, or Dr. Nafise Moosavi,
whose group's agenda is reliable LLM evaluation and who is already flagged in
the team notes as the highest-leverage medium-term contact. Those people
plausibly endorse for **cs.CL** or **cs.LG**; they may well not qualify for
**cs.CR**.

The paper's subject supports either framing. It is about evaluation validity and
benchmark saturation as much as it is about security. And critically: **the
register does not care which category the arXiv paper sits in** — it only needs
an arXiv URL.

So the pragmatic move is to pick the primary category by *who can endorse you*,
not by taste. cs.CL or cs.LG primary with a cs.CR cross-list is very likely
easier than cs.CR primary. (Whether a cross-list itself needs separate
endorsement is worth confirming before relying on it — I did not verify that.)

---

## 2. Gap analysis: report card → preprint

The report card ([`docs/findings/benchmark-quality-report-card.md`](./findings/benchmark-quality-report-card.md),
~3,000 words) already has: Abstract, RQ, Method, Results in three subsections,
Threats to validity, Related work, Limitations, Conclusion and future work, and
a Reproduce block. That is a paper's skeleton, already written.

| Element | State | Gap | Effort |
| --- | --- | --- | --- |
| Abstract | ✅ written, accurate, already carries the corrected κ claim | tighten to arXiv's character limit | ~1h |
| RQ / motivation | ✅ sharp, "discriminate" is the right operative word | none | — |
| Method | ✅ complete; METHODOLOGY.md is the source of truth | condense; move detail to appendix | ~half day |
| Results | ✅ three result sections, CIs, positive control, corrected κ table | needs the AgentDojo control (§4) | see §4 |
| Threats to validity | ✅ unusually good — detectable-effect floor, positive control, same-family judges, static-vs-adaptive, lower-bound render | none, this is a strength | — |
| Limitations | ✅ present and honest | none | — |
| **Related work** | ❌ **four bullets, zero formal citations** | **the single largest gap** — needs a real section and bibliography | **2–3 days** |
| **Bibliography** | ❌ **no BibTeX exists** | build from scratch, ~25–40 refs | included above |
| Figures | ⚠️ one (`results_matrix.png`) | needs a κ-degeneracy figure; possibly a defence-ablation figure | ~half day |
| LaTeX source | ❌ Markdown only | convert; Ross already ships LaTeX for CVs so the toolchain exists | ~1 day |
| Reproducibility statement | ⚠️ commands exist, but `results/` is gitignored | state the regeneration path and its API-key requirement plainly | ~2h |
| Author / affiliation | ❌ undecided | Sheffield-affiliated or independent — affects endorsement and may warrant a supervisor conversation | decision |
| Licence / ethics | ⚠️ repo MIT, ETHICS.md exists | pick an arXiv licence; add a sentence on the AGPL AgentDojo dependency | ~1h |

**Related work is the real writing task.** Going from "GCG, PAIR, TAP, HarmBench"
as bare names to a defensible section means actually reading the saturation,
LLM-as-judge-reliability, and inter-rater-agreement literature and positioning
against it. This is not formatting work and it cannot be short-cut.

---

## 3. The framing decision — and my recommendation

There is a choice here that changes how much extra work is needed, and it is
worth making deliberately.

**Framing A — "static jailbreak benchmarks have saturated."** This is how the
report card currently leads. The problem: it is not new. Benchmark saturation is
well-trodden, and with 2 targets and 2 corpora the study is thin as a saturation
paper. A reader's first question is "why only two models?", and there is no good
answer.

**Framing B — "inter-rater agreement is undefined on saturated benchmarks, and
the field reports the convention value as agreement."** This is the round-1
finding, and it is the most novel thing in the repo. It comes with:

- a clean formal statement (κ is `(po − pe)/(1 − pe)`; when both raters are
  constant `pe = 1` and κ is `0/0`),
- a worked example where it bit a *careful* project — this repo published
  "κ = +1.000 in all 12 cells" as validation, and 11 of those were degenerate,
- a demonstration that it propagates into a downstream composite metric
  (`judge_disagreement`, §5),
- and a constructive remedy: **ship a positive control**, which is exactly the
  differentiator the register listing would carry.

Under Framing B, small n stops being a weakness. You do not need fifty models to
show that a statistic is undefined; you need one worked case and the argument.
The saturation measurement becomes the *setting* that produces the degeneracy,
not the claim being defended.

**I would pick B**, with the saturation result as section 3 rather than the
headline. It is more defensible at this scale, it is more novel, it makes the
paper and the eval listing tell the same story, and it turns the repo's most
uncomfortable self-correction into its contribution.

**One optional addition would materially raise the paper's value:** a small
survey of how N published evals report judge agreement, and how many would hit
the same degeneracy at their reported base rates. That converts "we made this
mistake and caught it" into "this is a field-level reporting problem, here is
its prevalence." It is 2–3 extra days and it is the difference between a repo
write-up and something citable. It is also directly reusable as the register
listing's justification.

---

## 4. The AgentDojo positive-control hole

Carried over from `inspect-evals-port-scoping.md` §3.3, because in a paper it
becomes sharper.

A paper whose contribution is "evals should ship positive controls" has a
positive control on **AdvBench only**. The AgentDojo arm — the one that would be
registered — has none. A reviewer will find that immediately, and they will be
right.

Options, unchanged from the port scoping, but the paper raises the stakes on
picking (a):

- **(a) Run an AgentDojo positive control.** `llama2-uncensored:7b`, static
  injection corpus, n=50, no defences. $0 generation, ~$0.10–0.15 judge.
  **Risk:** the sibling `agent-redteam-replay` Gate-0 study killed a local-model
  arm because ≤8B models could not drive AgentDojo (16.7% vs a 75% capability
  gate) — if the model cannot do the user task, a low hijack rate measures
  incapacity, not resistance. Mitigating factor: that result was on the *live
  agent loop*; this is a *static render* with no tool-calling requirement, so the
  bar is materially lower. Unknown until run.
- **(b) Two tasks** — AdvBench with its existing control, AgentDojo without,
  documented.
- **(c)** AdvBench control relabelled as harness-level. Weakest.

### RESOLVED 2026-07-27: (a) ran and failed — and it improved the paper

Executed with the threshold pre-registered before the run. Judge ASR **2%**
against a PASS threshold of 20% (METHODOLOGY §12.6). Cost: $0.21.

It is not a resistance result. The model never refuses and confabulates rather
than reading the tool output (26% of responses cite emails absent from the
prompt), so the cell measures incapacity. The AgentDojo arm is therefore
**uncontrolled**, and the paper must say so.

That sounds like a loss and is not, for Framing B. It supplies three things the
paper did not have:

1. **A second worked example of the paper's own thesis.** A metric that looks
   like a safety measurement (ASR = 2%) is unattributable, exactly as κ = +1.000
   looked like agreement and was not. Same failure shape, different statistic.
2. **A constructive rule.** *A positive control needs its own capability gate* —
   the candidate must first be shown able to perform the benign task. That is a
   concrete, reusable recommendation, which a critique-only paper lacks.
3. **A recorded pre-registration error.** The secondary diagnostic tested for
   emptiness/refusal and the real failure mode was fluent confabulation, so it
   would have passed the run. Reporting that is itself an argument for
   pre-registration in eval work, and it is the kind of detail that makes a
   methods paper credible rather than self-congratulatory.

It also lands a third informative κ: this cell scores **+0.658**, tripping the
harness's own α ≥ 0.667 guard. So the project now has κ values at +0.935,
+0.658, and eleven undefined — direct evidence that κ *does* vary when there is
something to measure, which is the cleanest possible rebuttal to reading the
+1.000s as agreement.

**Net effect on the paper: the AgentDojo arm gets a stated limitation, and
Framing B gets a second case study.** No extra writing days; if anything the
contribution section is easier to write.

---

## 5. Dependency on the staleness decision

The paper cannot be written before the `judge_disagreement` question is settled
(see the separate decision put to Ross this round). §3.2 of the report card
currently documents the propagation but leaves the scoring unchanged. A paper
that identifies a degenerate-statistic problem and then ships a composite metric
still consuming the degenerate value is not a position worth defending in
print. Whichever option is chosen, it needs to be chosen and reflected before
drafting.

---

## 6. Effort estimate

Honest, focused-working-days, assuming Framing B:

| Task | Effort | Blocking? |
| --- | --- | --- |
| Secure an endorser | **wall-clock days to weeks; not your effort** | **yes — start now, in parallel** |
| Settle the staleness decision (§5) | ~half day if (b)/(c) chosen | yes |
| AgentDojo positive control run (§4) | half day | yes |
| Related work + bibliography | **2–3 days** | yes |
| Formalise the κ-degeneracy contribution | 1–2 days | yes |
| LaTeX conversion, figures, formatting | 1–1.5 days | yes |
| Reproducibility / licence / affiliation | ~half day | yes |
| *Optional:* prevalence survey of judge-agreement reporting | +2–3 days | no, but recommended |
| *Optional:* third-family judge to answer the same-family objection | half day + small API spend | no, but recommended |

**Total: 5–7 focused days to submittable without the optional work; 8–12 with
it.** Plus endorsement wall-clock, which is out of your hands and therefore
should be started first.

### The scheduling problem

The dissertation draft is due in 35 days and submission in 50. A 5–12 day
writing effort sits inside that window and competes for exactly the same
capability — sustained academic writing. Three ways through, in order of my
preference:

1. **Start the endorsement request now, defer the writing until after the
   dissertation.** Costs nothing, removes the longest-lead item from the critical
   path, and the paper starts the day the dissertation ships.
2. **Look for genuine overlap.** If any part of the dissertation covers
   evaluation validity or LLM-judge reliability, the related-work reading is
   shared and the 2–3 day estimate roughly halves. Worth ten minutes of checking
   before assuming there is none.
3. **Write the paper first.** Only if the dissertation is comfortably ahead of
   schedule. I would not recommend it.

The port and register submission are unaffected by this — they are gated on the
paper, and the paper is gated on the dissertation. Nothing is lost by sequencing
it that way, provided the endorsement request goes out now.

---

## 7. Recommendation

1. **This week, costing nothing:** identify an endorser and send the request.
   Decide primary category by who can endorse (§1.3), not by taste.
2. **Half a day, ~£0.15:** run the AgentDojo positive control. Its outcome
   changes the paper either way.
3. **Settle the staleness decision** (separate, this round).
4. **Defer the drafting until after the dissertation**, then write to Framing B
   with related work as the main task.
5. **Do the prevalence survey if the time exists.** It is what makes the paper
   citable rather than a well-documented repo.

## Sources

- [arXiv endorsement help](https://info.arxiv.org/help/endorsement.html)
- [arXiv endorsement policy update, 21 Jan 2026](https://blog.arxiv.org/2026/01/21/attention-authors-updated-endorsement-policy/)
- [inspect_evals register submission guide](https://github.com/UKGovernmentBEIS/inspect_evals/blob/main/register/README.md)

All fetched 2026-07-27.
