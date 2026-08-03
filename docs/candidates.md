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

**Status:** blocking a release. Assigned elsewhere; **not** to be fixed in
isolation.

Both are the same class — *the artifact is not the repository* — and both fire on
the same event, a release build. Fixing either alone produces a release that is
still wrong, just wrong differently.

### 1. No sdist allowlist

The build has no explicit include list, so the packaged sdist is determined by
exclusion. Hatchling reads the **repository's** `.gitignore`, not a global one,
so local-only directories present in a working tree are packaged on the next
release. A sibling repository leaked exactly this way, and its fix plus the test
that enforces it exist there as a working reference.

### 2. Eighteen relative README links break on PyPI

`README.md` is the package `long_description`. It carries **18 distinct relative
targets** that resolve on GitHub and break on PyPI:

```
./CHANGELOG.md   ./CONTRIBUTING.md   ./ETHICS.md   ./LICENSE
./METHODOLOGY.md   ./METHODOLOGY.md#12-threats-to-validity
./docs/ROADMAP.md   ./docs/inspect-evals-port-scoping.md
./docs/preprint-scoping.md   ./pyproject.toml   ./reports/samples/
./tests/README.md   ./uv.lock   docs/results_matrix.png
./docs/findings/benchmark-quality-report-card.md
./docs/findings/what-does-this-metric-return-when-nothing-happened.md
./docs/findings/what-mechanical-conversion-does-to-taiwan-native-safety-text.md
./docs/findings/a-preregistered-null-at-p-0-0001.md
```

Two of those matter more than the rest. `./LICENSE` is wrapped inside the licence
badge, so a naive link scan that only looks at the outermost `[text](target)` per
line can miss it. And **`docs/results_matrix.png` is the headline figure** — on a
package page it renders as a broken image in exactly the place the finding's
evidence belongs. A sibling repository shipped that and had to cut a patch
release to correct it.

### Why they must land together

A release with the allowlist fixed but the links unfixed shows a broken headline
figure. A release with the links fixed but the allowlist missing leaks local
files. Neither is shippable, so neither fix is complete on its own.

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
