# Named candidates — not started, not designed

Questions this repository has surfaced and deliberately not pursued. Each is
recorded with what it would require, so the decision to start one is a decision
rather than a drift.

**Nothing here is scoped, designed, or begun.** A candidate becomes work only
with an explicit decision, and — where it requires spend — a costed figure
approved in advance.

---

## Does vocabulary localisation change model *rankings*?

**Status:** candidate. Not started.

**Where it came from.** The locale-provenance study found its guard classifier
sensitive to Taiwan **vocabulary** (`TWPhrases`) rather than to character
variants, and refuted the character-level mechanism it had predicted. That makes
a different question live: if one model's safety behaviour moves with
vocabulary localisation, do *different models move differently* — enough to
reorder a leaderboard?

**Why it is not a continuation.** The preregistered study reported a null on its
primary outcome, and its follow-on tier is NO-GO on that basis. This is not the
same question measured better; it is a **new question with a new primary
outcome**, and it needs its own preregistration written before any model runs.
Treating it as a continuation would let a null be walked back into a positive by
changing the outcome after seeing the data — the exact failure the
preregistration exists to prevent.

**What it would require, at minimum:**

- **Multiple target models.** A ranking needs things to rank. One guard
  classifier cannot produce one, so this is a **spend decision**, not a local
  run.
- A new preregistration: primary outcome, minimum effect fixed in advance,
  kill criteria, and a stated multiple-comparison plan — the current
  preregistration has none, which is fine for one primary contrast and not fine
  for a ranking across models.
- Cross-family judges, for the reasons already recorded in the existing
  preregistration.
- A costed plan with a figure approved before anything is called.

**Why it might be worth it.** "Leaderboards reorder depending on how prompts
were rendered" is a benchmark-validity claim that anyone publishing a
leaderboard has to care about, and it does not depend on the effect size that
failed the existing study's bar.

---

## bf16 versus 4-bit as a finding in its own right

**Status:** conditional. Becomes a candidate only if the bf16 confirmation run
disagrees with the 4-bit run.

Guards are commonly deployed quantised. A guard whose verdicts move with its own
precision is an instrument reporting its compression, which would be a result
worth its own write-up. The analysis plan fixed before the confirmation run
(`docs/bf16-confirmation-plan.md`) states what is reported in each case, so
neither outcome can be selected after the fact.

If the two precisions agree, there is no candidate here — only a caveat deleted.

---

## Packaging: two defects that must land together before any release

**Status: landed in 0.4.0.** Both fixed in one change, as required — a release
with only one of them fixed is still a wrong release, just wrong differently.

The sdist is now an allowlist that fails closed, and every README link is
absolute. Both are enforced against the built artifact rather than the source
tree: `tests/unit/test_sdist_contents.py` builds the sdist and fails on any
member git does not track, and `tests/unit/test_readme_links.py` matches on link
targets so it sees the ones nested inside a badge.

Two things found while fixing it are recorded in
[the absence catalogue](findings/what-does-this-metric-return-when-nothing-happened.md)
rather than here, because they are findings and not candidates: this repository
was itself packaging untracked files, and its release workflow runs no tests.

---

## Upstream report: `transformers` weight-placement segfault

**Status:** candidate. Not filed.

`transformers` 5.14.1 segfaults during weight placement for an 8B Llama
checkpoint on the development host under every `device_map` — auto, explicit
single-device, quantised and unquantised alike — while 4.57.6 loads the same
checkpoint on the same GPU without incident. Basic CUDA is unaffected, and it is
not a capacity limit.

Filing it upstream is a decision to make a public report against another
project, and it is not this repository's to make unilaterally. The pin and its
reason are recorded in `pyproject.toml` so the local situation is safe either
way.
