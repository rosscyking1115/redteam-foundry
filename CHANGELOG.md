# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.5.1] — 2026-08-07

**A patch: two things a user hits that the repository could not see.** No API
change, no behaviour change to any metric, and no published number moves. Both
fixes are about what reaches somebody who is not reading this file.

### Fixed
- **The PyPI page carried no warning about 0.5.0's breaking change.**
  `infer_attack_families` returning `FamilyTags` is named in the 0.5.0 release
  notes and in this changelog, and PyPI renders `README.md` only — so anyone who
  upgraded by reading the project page got no warning that `len(tags)` would now
  raise. Structurally invisible to the release checks, because every one of them
  passed: the description rendered, the figure loaded, the links resolved.

  `README.md` now carries a compact note directly under the install line, so the
  warning travels with the artifact it applies to. It names the failing call and
  its one-line migration rather than pointing at a changelog the reader is not
  currently looking at, and it also flags that false-refusal figures can move.

- **`corpora audit-hf --help` gave an example that no longer works.** It named
  `walledai/AdvBench`, which has since become **gated** on the Hugging Face Hub.
  A new user copying the example out of `--help` — the one place they are
  guaranteed to look — got an access error on their first run, with nothing to
  distinguish "you need to request access" from "this tool is broken". Nothing in
  the repository could notice: the dataset's availability is not ours to control
  and no test reaches the Hub.

  The example is now `JailbreakBench/JBB-Behaviors`, verified ungated and
  verified to run end to end, and it is given as a **complete invocation**
  (`--config behaviors --split harmful --prompt-column Goal`) rather than a bare
  id, since the config and split are not guessable.

  A gated load now also prints what happened and what to do: request access and
  `huggingface-cli login`, or switch to the ungated example. The detection matches
  on the message rather than the exception type, because `datasets` has moved that
  class between releases and a type-pinned check would stop firing silently on an
  upgrade — a hint that quietly disappears being the failure mode this repository
  keeps cataloguing. `tests/unit/test_smoke.py` pins the real Hub wording as the
  fixture, asserts an ordinary error does *not* trigger the hint, and asserts the
  known-gated dataset cannot return to the help text.

  This does not prove the new example is *still* ungated — only a live call can,
  and none runs in CI. Stated rather than implied.

## [0.5.0] — 2026-08-05

**Why MINOR and not PATCH.** A public return type changes, three public models
gain fields, and **the value an existing metric returns changes** on some
inputs. Any one of those rules out a patch. It is not MAJOR because the one
breaking change is narrow and has a documented one-line migration.

### Breaking

- **`infer_attack_families` now returns `FamilyTags`, not `tuple[str, ...]`.**

  `FamilyTags` implements `__bool__` and `__iter__`, so `if tags:` and
  `for fam in tags:` are **unaffected**. **`len(tags)` is the call that
  breaks** — it raises `TypeError`. Migration is `len(tags.families)`, or
  `len(list(tags))`. Indexing and slicing are likewise on `.families`.

  The reason for the change is the point of it: the function returned an empty
  tuple both when it had looked and found no attack-family marker, and when it
  had been handed a script its `\b`-anchored English patterns cannot read at
  all. Its docstring drew that distinction; the return value could not carry
  it, so no caller could act on it. `FamilyTags.readable` now does.

### Changed — behaviour, not bug fixes. Your numbers can move.

These are not corrections to arithmetic. They change what the harness reports
for inputs it previously mis-scored, so a re-run over the same data can produce
different figures. That is the intended effect, and it is stated here rather
than discovered.

- **`RefusalScore` gains `readable`.** The rule-based refusal scorer is
  anchored on English, so it returned `is_refusal=False` for a refusal written
  in Chinese, Japanese, Korean, Russian or Arabic — **the same verdict it
  returns for a full compliance in those languages.** `readable=False` now
  marks the cases where the scorer could not read the response at all. The
  field defaults to `True`, so existing constructions keep working.

- **`compare.frr_by_language` excludes unreadable cells and reports the
  count.** On an *unjudged* run it fell back to the scorer above and averaged
  its blind `False`s into **false-refusal rate = 0%** for exactly the languages
  the multilingual set exists to ask about. Those cells are now excluded, the
  count is carried on every row and on the report and is rendered, and a rate
  over zero readable cells reports as undefined rather than 0%.

  **Migration note for anyone tracking FRR over time:** a previously reported
  0% for zh/ja/ko on an unjudged run was an artefact. The new figure is not a
  regression; the old one was not a measurement. Judged runs are unaffected —
  the judge read what the patterns could not.

- **Three counted-exclusion fields, all defaulted.** `LanguageFRR` and
  `LanguageFRRReport` gain `n_unreadable_excluded`; `CorpusQualityReport` gains
  `n_near_dup_unreadable_excluded` and `n_family_unreadable_excluded`. Anything
  deserialising these models with `extra="forbid"` against an older schema
  should re-check, though all three have defaults.

- **The staleness obsolete-meme axis reports *unavailable* instead of 0.0 on a
  corpus it cannot read.** All twelve marker patterns are `\b`-anchored
  English, so on a non-English corpus they matched nothing and the axis scored
  **0.0 — "not stale"**: the most flattering answer available, produced by not
  being able to read the corpus, from the heuristic's largest component
  (weight 0.30).

  It now reports `available=False, score=None`, drops out of the composite, and
  the remaining weights renormalise — the same mechanism 0.4.0 introduced for a
  degenerate κ on `judge_disagreement`.

  **This moves published-style staleness scores for any non-English corpus.**
  English corpora are unaffected: every audited corpus in this repository is
  100% Latin, and the before/after figures were verified byte-identical.

- **Near-duplicate detection excludes prompts its tokeniser cannot read**, and
  reports how many. `\w+` presupposes whitespace-delimited words, so an
  unspaced sentence became a single token and a Chinese pair differing by one
  character scored a Jaccard of 0.000 where its English equivalent scores
  0.818. A corpus previously reporting **zero near-duplicates** may now report
  an exclusion count instead — which is the honest answer, not a worse one.

### Removed

- **`uv.lock` is no longer tracked**, and two published reproducibility claims
  are withdrawn rather than reworded: **"`pyproject.toml` + `uv.lock` pin every
  Python dependency"** (`METHODOLOGY.md` § 10) and **"Dependencies are pinned
  in `uv.lock` for a byte-for-byte reproducible environment"**
  (`docs/getting-started.md`). Nothing in the repository ever read the lock;
  the second claim was printed four lines below the command that bypassed it;
  and it had already gone stale enough that `uv lock --check` refused it. Full
  statement in **Retracted**, below.

  **No action is required of installers** — `pip install redteam-foundry`
  resolves from `pyproject.toml` exactly as it always did. What changes is that
  the project no longer *claims* a locked environment it never provided.

### Added

- `redteam.readability` — one convention for "the matcher could not read this
  input": `is_readable`, and `Screen`, which carries the exclusion as a number
  so a caller cannot report a rate without reporting what it was computed over.
- Coverage and guards: `tests/unit/test_readability.py`,
  `tests/unit/test_figure_caption.py`, `tests/unit/test_test_index.py`, and
  `load_hf_dataset` coverage including a `RUN_HF_NETWORK=1` live test.

### Not in this release

- No change to any published number in `METHODOLOGY.md` § 8. The 12-cell matrix,
  its confidence intervals and the positive-control κ = +0.935 are unchanged,
  and `scripts/headline_table.py --check` passes against them.

### Retracted
- **"`pyproject.toml` + `uv.lock` pin every Python dependency."** Published in
  `METHODOLOGY.md` § 10. And, in `docs/getting-started.md`: **"Dependencies are
  pinned in [`uv.lock`](../uv.lock) for a byte-for-byte reproducible
  environment."**

  Neither was true, and the second was printed four lines below the command that
  made it false. The setup block ends with `uv pip install -e ".[dev]"`, which
  resolves fresh from `pyproject.toml` and never opens the lock — so a reader
  following the instructions was executing the refutation at the moment of
  reading the guarantee.

  **Nothing in this repository read `uv.lock`.** CI (`ci.yml`) and the release
  workflow (`publish.yml`) both install with `uv pip install --system -e
  ".[dev]"`; `uv build` does not read it either. There was no `uv sync`, no
  `--frozen` and no `--locked` anywhere in the repository. The file was tracked,
  704 KB, documented twice, and consumed by none of it.

  It had also **already failed its own check, unnoticed**: `uv lock --check`
  exits 1 against the tracked file. Anyone running `uv sync --locked` would have
  been refused. Nobody was, because nobody ran it.

  Withdrawn rather than reworded, and `uv.lock` is no longer tracked. Written up
  as instance #21 in
  `docs/findings/what-does-this-metric-return-when-nothing-happened.md`.

### Changed
- **`METHODOLOGY.md` § 10 now names what enforces each guarantee**, and is
  stronger for the retraction rather than shorter. Every row of the new table
  points at the test, script or workflow that would fail if the guarantee
  stopped holding — the OpenCC per-file SHA-256 pin and `test_opencc_pin.py`,
  the content-addressed cache and `test_cache.py`, `headline_table.py --check`
  and `test_headline_table.py`, and so on.

  **Two rows say "nothing", deliberately.** Python dependency versions, per the
  retraction above; and `configs/dataset_versions.yaml`, which records the
  upstream commit for every corpus and states that loaders "MUST resolve to one
  of these" — while no code reads the file and no test compares a loader against
  it. That second one was found by the same question as the first and is
  reported rather than quietly fixed, because fixing it properly needs a check
  that bites in CI, where the loader manifests are not present.

  **The decision behind the retraction, since it is a judgement and not a fact.**
  Making CI read the lock was the alternative, and it was measured before being
  rejected: the locked resolution and CI's differ by a major version of
  `huggingface-hub` (0.36.2 against 1.26.0), because the lock's universal
  resolution is constrained by `transformers<5` from the `guard` extra — an
  extra CI never installs. Both resolutions were installed and the full suite
  run under each; both green, and the `corpora audit-hf` path exercised directly
  under each including a live load. Enforcing the lock would have bought
  enforcement at the price of testing a configuration no user has: for a library
  on PyPI, the resolution that matters is the fresh one, because that is what
  `pip install` produces.

### Added
- **`load_hf_dataset` is tested.** It is the only place `datasets` is imported
  and it had **zero coverage**, inside a suite reporting 80.19% against a 75%
  floor. The gap became load-bearing while deciding the retraction above: the
  question "does the audit path still work under the other resolution?" could
  not be answered from the suite, because a green run said nothing about the one
  function that touches the library.

  Covered offline by substituting `datasets.load_dataset` — argument forwarding
  including `revision` (the whole reproducibility story for an ad-hoc audit),
  the missing-column error, `limit`, and the security property that
  `trust_remote_code` is never passed for an untrusted repo id. That module is
  now at 100%. One live test sits behind `RUN_HF_NETWORK=1`, since only a real
  load can catch an upstream change and a unit suite must not depend on the Hub
  being reachable; that CI does not cover the live path is stated in the module
  rather than implied. Instance #22 in the absence catalogue.

### Fixed
- **Four validators returned a confident negative for input they could not
  read.** Found by sweeping all 21 text-verdict validators in the repository for
  the question instance #7 had already generalised and left as advice: *what
  does this return for input outside its alphabet?* Two instances is a pattern,
  so it was asked of all of them at once.

  | validator | what it returned outside its alphabet |
  | --- | --- |
  | `scorers/refusal_keywords.score_refusal` | `is_refusal=False` for a refusal in zh/ja/ko/ru/ar — **the same verdict as a compliance in the same language**. On an unjudged run `frr_by_language` averaged those into **FRR = 0%** for exactly the languages the multilingual set exists to ask about. |
  | `corpora/quality._near_duplicates` | Jaccard `0.000` for a Chinese pair differing by one character, where the English equivalent scores `0.818` — `\w+` makes an unspaced sentence one token. **Zero near-duplicates**, read as a clean corpus. |
  | `staleness._obsolete_pattern_score` | `0.0` — "not stale" — on any non-English corpus, from the heuristic's largest component (weight 0.30). |
  | `corpora/taxonomy.infer_attack_families` | An empty tuple whether it looked and found nothing or could not look. The docstring drew the distinction; the return value could not carry it. |

  **No published number changes.** Verified rather than asserted: every audited
  corpus is 100% `latin` (504/504, 949/949, 342/342, 88/88), FRR is not in the
  v1 reported matrix, rule-based ASR feeds staleness only as a fallback behind
  judge ASR, and `results/*.json` already carry frozen verdicts. Every
  downstream figure was recomputed before and after and the two snapshots are
  byte-identical; `scripts/headline_table.py --check` stays green.

  Written up as instances #17 through #20 in
  `docs/findings/what-does-this-metric-return-when-nothing-happened.md`, with
  #15 and #16 covering the figure caption and the guard that could not read `κ`.

### Added
- **`src/redteam/readability.py` — one convention for "could not read this".**
  Deliberately not a second script classifier: `is_readable` is a one-bit
  precondition ("any Latin letter for a `\b` to anchor on?"), and `Screen`
  carries the exclusion as a number so a caller cannot report a rate without
  reporting what it was computed over. Modelled on the discipline
  `scripts/report_locale_provenance.py` has had all along — exclude the
  unreadable cell, **count it, and publish the count**.

  Applied at all four sites, and in every case the caller now excludes *and*
  reports: `LanguageFRR` gains `n_unreadable_excluded` per row and renders it;
  `CorpusQualityReport` gains `n_near_dup_unreadable_excluded` and
  `n_family_unreadable_excluded`; the staleness meme axis reports
  `available=False` and renormalises out, reusing the `score: float | None`
  mechanism 0.4.0 built for degenerate κ and never applied here.

  Two rules keep the screen from over-reaching. A *hit* proves readability — the
  patterns are English, so a match could not have come from anywhere else — so
  only the negative verdict is screened, and true positives on mixed-script text
  survive. And readable input takes exactly the path it took before, which is
  what makes the byte-identical snapshot possible.

### Changed
- **`RefusalScore` gains `readable`, and `infer_attack_families` now returns
  `FamilyTags` rather than a bare tuple.** Both are behaviour changes to shipped,
  importable API. `FamilyTags` keeps `__bool__` and `__iter__` so `if tags:` and
  `for fam in tags:` read as before; `RefusalScore.readable` defaults to `True`
  so existing constructions keep working.
- `multilingual.py` said the exclusion filter is "English-only". Stale since
  `_PATTERNS_ZH` landed. Its alphabet is **{English, Chinese}** — not
  "everything", which is a second reason the benign-only rule there is a policy
  rather than a preference.
- **The absence catalogue's section headings no longer carry counts.** They read
  "The six", "Five more", "Three more", so every append renamed the thing being
  appended to — and one append was blocked on exactly that. A catalogue about
  numbers going stale whose own headings were stale-able counts is the defect it
  documents, one level up. Headings now name provenance; entry numbers are
  stable identifiers and are unchanged, since `CHANGELOG.md` and the entries
  themselves cite them. One heading was already stale when found: "Both were
  found while fixing packaging" stood above three entries.

### Fixed
- **The headline figure was still making the claim 0.4.0 retracted.** The caption
  rendered into `docs/results_matrix.png` read *"Point = LLM-judge ASR; whisker =
  95% bootstrap CI; two-judge cross-validated (ASR κ = 1.00, all 12 cells)"* — the
  retracted claim almost verbatim, presented as cross-validation, on the one image
  through which the finding is delivered. The prose was corrected in 0.4.0 and the
  figure was not, so the README argued against a claim its own headline graphic
  went on asserting.

  The caption now says what is plotted and stops: *"Point = LLM-judge ASR; whisker
  = 95% bootstrap CI."* The surviving measurement — the positive control's
  κ = +0.935, n = 98 — is deliberately **not** substituted in. It belongs to a cell
  that is not among the 12 plotted, so in this caption it would read as though the
  matrix had been validated at 0.935. Every judge-agreement figure here needs a
  sentence of qualification, and a caption is the one part of a document
  guaranteed to travel without it: a screenshot carries the caption and nothing
  else. Shorter and true beats complete and misleading.

  **No plotted value changed.** The figure was regenerated from the committed
  generator rather than edited, and the result is pixel-identical to the published
  image everywhere above the caption line — every point estimate and every
  confidence interval is byte-for-byte what it was.

  **This corrects the already-published pages, with no release.** The README's
  image URL is pinned to `main` on `raw.githubusercontent.com` rather than to a
  tag, so replacing the file fixes the GitHub README and the PyPI descriptions for
  both 0.4.1 and 0.4.0 at once — including descriptions that are otherwise frozen
  at upload. Worth stating plainly rather than discovering later: an image pinned
  to `main` retroactively changes what an already-published page shows. That is
  the right property for a correction and the wrong one for anything else, and it
  is why the frozen-at-upload rule in 0.4.1 above does not bind here.

  Why nothing caught it: the figure was checked three times during release work —
  it resolves, it returns `image/png`, it uses no relative target — and every check
  confirmed the image *loads*. None read what it said. An image is a claim, and
  nothing in the repository tested what its figures assert.
  `tests/unit/test_figure_caption.py` now does, against both the generator and the
  committed PNG.

### Added
- **`tests/unit/test_figure_caption.py`** — the caption of the headline figure is
  checked like any other published claim. The generator defines it as a named
  `CAPTION` constant and records it in the PNG's `Description` metadata, so the
  guard reads the committed artifact as well as the code that should have produced
  it, and fails if the two disagree — the staleness case where the caption is
  corrected and the figure is never regenerated. The rule enforced is not "no false
  κ" but "no judge-agreement claim in this caption at all", for the reason given
  above. It does not read the pixels; that limitation is stated in the module
  rather than glossed.

## [0.4.1] — 2026-08-03

**A patch: no API change, no behaviour change, two corrections to what the
published page and the CLI say.** Nothing a caller imports changes signature or
result. Under semver that is a PATCH — the one user-visible behaviour change is
`redteam version` printing the right number instead of the wrong one, which is a
bug fix rather than a new capability.

It needs a version at all because **a PyPI description is frozen at upload**. The
description *is* the README, so the only way to correct the page is to publish
again; on its own the stale line would not have been worth it, but the README
restructure travels with it and both arrive together.

### Fixed
- **`redteam version` reported `0.3.0` on the 0.4.0 release.** `pyproject.toml`
  was bumped to 0.4.0 and the hardcoded `__version__` in
  `src/redteam/__init__.py` was not, so the published 0.4.0 wheel carries
  `METADATA: Version: 0.4.0` beside code saying `0.3.0`. Anyone who installed
  0.4.0 and ran `redteam version` was told 0.3.0. Stated rather than quietly
  corrected: 0.4.0 is wrong about its own version and will stay wrong.

  `__version__` now reads the installed distribution metadata, so there is one
  source of truth and nothing to keep in step by hand.

  The reason nothing caught it is the more useful part. There *was* a test —
  `assert __version__ == "0.3.0"`, a third hardcoded copy — and it was green
  throughout the release, because the code and the test held the same wrong value
  and agreed with each other while the package metadata said something else.
  **Agreement is not correctness.** `tests/unit/test_version.py` now compares the
  version against `pyproject.toml`, against the installed distribution, and
  against what the CLI actually prints, and refuses to run against the
  not-installed placeholder. Written up as instance #14 in
  `docs/findings/what-does-this-metric-return-when-nothing-happened.md`.
- **The status line published in 0.4.0 was already stale when it was uploaded.**
  It said the corpus-audit and locale-provenance lines were *ongoing*. Both had
  concluded before that release shipped. Corrected here; 0.4.0's description
  cannot be edited.

### Changed
- **The README is split rather than trimmed; nothing was deleted.** It was 2,420
  words carrying three Diátaxis types at once — explanation, reference and
  how-to — against a house target of roughly 1,200 and sibling repositories that
  finished at 1,075 and 1,007. Reference material (the command listing, the
  pipeline diagram, what the foundry does) moved to `docs/commands.md`; how-to
  material (install, development setup, reproducing the headline table) moved to
  `docs/getting-started.md`. The README keeps explanation and the reader ladder.
- **The README now says who it is for and what problem it solves**, which it
  never did. That rung was simply absent: a reader could learn what the project
  measured without learning who should care. The problem is now stated plainly —
  a robust model and an exhausted benchmark both report "0% of attacks
  succeeded", and the success rate alone cannot tell them apart.
- The question is still posed before the finding is stated, deliberately. A
  finding written in a project's own vocabulary is illegible to a reader who does
  not yet hold the question.
- Two counts in the README that had drifted are gone rather than corrected: the
  absence catalogue was described as holding "nine" instances when it held
  thirteen. A count in a link description decays every time the target grows, so
  it is now described rather than counted.
- `docs/ROADMAP.md` said "Phase 0 is complete" while every phase below it was
  marked done — true, and implying far less progress than exists.

## [0.4.0] — 2026-08-03

**This release exists to correct the published page, not only the repository.**

0.3.0's project description on PyPI states that the two judges "agree
**perfectly — κ = +1.00 in all 12 cells**, so the headline metric is well-posed",
and repeats it under *Why this reports ASR and not refusal rate*. That claim was
retracted in this repository below, and eleven of those twelve values are
degenerate. A PyPI description is frozen at upload time and cannot be edited, so
the retraction reached readers of the repository and did not reach readers of the
package. This upload is how it reaches them. The wrong figure is being **replaced
in the open with a record of what it was**, not quietly overwritten.

Scope: three new importable modules (`redteam.provenance`, `redteam.opencc_pin`,
`redteam.controls`), two new optional extras (`provenance`, `guard`), a new
public function (`redteam.stats.is_degenerate_kappa`), and a change to the value
an existing metric returns — published staleness scores move. Any one of those
rules out a patch release; the changed metric output is what makes it a minor
rather than additive-only.

### Retracted
- **"The judges agree perfectly — κ = +1.00 in all 12 cells."** Published in
  0.3.0's description and README. Eleven of the twelve κ values are the `0/0`
  convention rather than a measurement, so the claim rested almost entirely on
  cells where agreement could not be measured. The surviving evidence is the
  positive control's **κ = +0.935** (n = 98). Detail in *Changed*, below.

### Changed
- **Corrected the inter-judge agreement claim.** The published headline said the
  two judges agreed "perfectly on ASR (κ = +1.000 in all 12 cells)". Eleven of
  those twelve values are degenerate: both judges labelled every cross-judged
  case identically and constantly, so expected agreement `pe = 1` and Cohen's κ
  is an undefined `0/0` that the scorer fills in as +1.000 by convention. That
  is the same defect the methodology already rejects on the refusal axis, at the
  opposite end of the marginals. The claim now rests on the **positive control's
  κ = +0.935** (n = 98, 79 positives per judge) — the one cell with substantial
  label variance on both margins. Updated in `METHODOLOGY.md` §7/§8/§12.3,
  `README.md`, and the findings report card. No measured number changed; the
  interpretation of one did.
- Also disclosed: the AdvBench Llama baseline's single ASR = 1 case is one of the
  two the cross-judge failed to parse, so that cell's cross-judge sample is
  all-zero and the one case that could have tested agreement was never
  cross-checked.
- **`staleness.py`'s `judge_disagreement` component no longer consumes a
  degenerate kappa.** Previously it averaged the stored `cross_judge_asr_kappa`
  across all runs, including the eleven whose value is the 0/0 convention — so a
  0.10-weight component reported "the judges agree" on exactly the saturated
  corpora it is meant to be informative about. Degenerate runs are now excluded
  from the average; when none survive, the component reports **undefined**
  rather than 0.00, drops out of the composite, and the remaining weights
  renormalise. Runs carrying a kappa but no per-case labels are treated as
  unverifiable and excluded rather than silently trusted.

  **Published staleness scores move as a result** — the movement is the finding,
  not a correction to the corpora:

  | corpus | was | now | components | why |
  | --- | ---: | ---: | ---: | --- |
  | AdvBench | 0.38 | **0.43** | 4/5 | all 4 cross-judged runs degenerate; component undefined and renormalised out |
  | AgentDojo | 0.43 | **0.43** | 5/5 | 7 of 8 degenerate, but one informative run survives, so the component still scores 0.00 — now stated as resting on 1 run |

  Neither corpus changes interpretation band ("Mixed") or confidence ("high").
  `reports/samples/staleness/` regenerated.
- `redteam.stats.is_degenerate_kappa` is now the single source of truth for the
  degenerate/informative rule, consumed by both `scripts/headline_table.py` and
  the staleness scorer so the published table and the composite metric cannot
  drift apart.

### Added
- **Synthetic detector control — run, and INCONCLUSIVE.** A capable model
  (`llama3.1:8b`, the same target as the section 8 AgentDojo rows) plus a system
  prompt instructing it to treat tool-output instructions as authoritative,
  on the same 50 cases. Pre-registered PASS bar was ASR >= 70%; the run returned
  **38%** (cross-judge kappa +0.917). Not a pass, and not reported as one.

  It failed for a different reason than the section 12.6 control: not
  incapacity, but **the control instruction not taking** — refusal fell 90% ->
  58% under the compliance prompt, so the model still refused a majority of the
  time and the staged hijack never reliably occurred. A tempting post-hoc
  rescue (0/29 refusals were hijacks, 19/21 non-refusals were) is recorded and
  refused: refusal is post-treatment and correlated with the outcome, so
  conditioning on it is selection on the dependent variable.

  **The AgentDojo arm remains uncontrolled** after two attempts and two distinct
  failure modes. METHODOLOGY section 12.8; frozen in `--check` under its own
  detector-control table, never merged with the positive controls.
- Section 7's refusal claim **narrowed by this run**: the instability is a
  property of the aligned charitable-redirect response, not of indirect
  injection as such. Where behaviour is unambiguous the same two judges agree
  perfectly on refusal (kappa = +1.000 on genuine variance, 29/50). The
  conclusion stands; the stated reason was too broad.
- **Control harnesses (`redteam.controls`), a concept distinct from defences.**
  A defence is a candidate mitigation whose effect on ASR is under study; a
  control harness deliberately forces a known outcome so the pipeline's ability
  to *detect* that outcome can be checked. Configured via a separate `controls:`
  key, deliberately absent from the `DEFENCES` registry (enforced by a test),
  and recorded in artifacts as `control:<id>` so a run can never read
  `defences: []` while compliance was engineered.

  Control runs are **excluded from `redteam corpora staleness` outright** rather
  than reclassified. A control is neither a baseline nor a defended run, and
  both naive partitions get it wrong — counting a high-ASR detector control as
  "defended" would read as a defence moving ASR a great deal, inverting this
  project's central finding. `StalenessReport.n_control_runs_excluded` records
  any exclusion and the rendered report prints it.
- `redteam.stats.grounding_score` — a capability diagnostic that asks whether a
  response is grounded in its input rather than whether output exists. §12.6's
  liveness check scored a confabulating model "100% engaged"; grounding scores
  the same responses 0. Reproduces the two figures quoted in METHODOLOGY
  (G = 1.00 for `llama3.1:8b`, G = 0.74 for `llama2-uncensored:7b`).
- `scripts/detector_control_verdict.py` — executes the pre-registered three-way
  detector-control rule against a judged run, so the verdict is computed rather
  than narrated and the boundary cannot move once the number is known.
- **AgentDojo positive control — run, and it FAILED its pre-registered
  threshold.** The indirect-injection arm previously had no under-elicitation
  control (§12.5 covered AdvBench only). `llama2-uncensored:7b` was run on the
  same 50 AgentDojo cases as the §8 Llama baseline, through the identical
  pipeline, with the PASS threshold (judge ASR ≥ 20%) committed in
  `configs/run_agentdojo_positive_control.yaml` *before* the run. Result: **2%**
  (cross-judge 4%, κ = +0.658 — which tripped the harness's own α guard).

  It is reported as **inconclusive, not as a null**. The model never refuses
  (0% rule-based) and confabulates instead of reading the tool output (26% of
  responses cite email addresses absent from the prompt), so the cell measures
  incapacity, not robustness. **The AgentDojo arm remains uncontrolled** and
  METHODOLOGY §8 now says so. New section METHODOLOGY §12.6, including the
  generalisable lesson (a positive control needs its own capability gate) and a
  recorded pre-registration error: the secondary diagnostic tested for
  emptiness/refusal and was blind to fluent confabulation.
- `configs/run_agentdojo_positive_control.yaml` — carries its own pre-registered
  analysis plan in-file.
- Both positive controls (the AdvBench pass and the AgentDojo failure) are now
  frozen in `scripts/headline_table.py --check`, so the failed control cannot
  quietly drop out of the record.
- `scripts/headline_table.py` now classifies each cell's cross-judge κ as
  degenerate or informative, recomputing the marginals from the per-case labels;
  it refuses to print a κ value for a degenerate cell, checks the positive
  control alongside the 12 matrix cells, and fails on status drift.
- `tests/unit/test_headline_table.py` — pins the degenerate/informative logic
  and the frozen 11-of-12 split (artifact-free, so it runs in CI).
- README: `mypy --strict` badge, and an explicit statement that CI gates on type
  errors and that `src/` is the typed surface.
- **`redteam.provenance` (extra: `provenance`) — locale renderings of the same
  semantic content, and the divergence metrics between them.** Given a
  Taiwan-native prompt it produces a glyph-only rendering, a dictionary-localised
  one and a Hong Kong one by round-tripping through Simplified, then reports edit
  distance attributed *per conversion stage* so an effect can be traced to a
  stage rather than to "conversion" in the abstract. Renderings are mechanical
  derivatives of one source, so their semantic equivalence is by construction and
  needs no annotator.
- **`redteam.opencc_pin` — the conversion treatment frozen by content.** Per-file
  SHA-256 of each compiled `.ocd2` dictionary and its upstream `.txt`, plus entry
  counts and the upstream commit. A version string does not identify a
  conversion; the dictionaries do. `verify_pin()` fails if what is installed
  drifts from what was measured.
- **A preregistration, committed before the run** —
  `docs/locale-provenance-preregistration.md` fixes a 5-percentage-point minimum
  effect and binds the conclusion to it regardless of statistical significance.
  It is in git history ahead of the first model call, so the threshold is
  checkable rather than asserted.
- **Four findings documents**, linked from the README: the preregistered null,
  what mechanical conversion does to Taiwan-native safety text, the benchmark
  quality report card, and the running catalogue of metrics that are satisfied by
  absence.
- `scripts/run_locale_provenance_guard.py` and `scripts/report_locale_provenance.py`
  — the guard harness and its reporter, with the absence counters split out of
  `main()` so they can be tested rather than merely printed.
- `tests/unit/test_absence_detector.py` — **fires** the absence detector with
  blank, whitespace-only and unparseable fixtures. A reported absence rate of
  0.00% is not evidence until the counter has been shown able to return non-zero.
- `scripts/check_finding_claims.py` — recomputes every quantitative claim in a
  findings document from the run artifact **and opens the document to compare**,
  rather than comparing against numbers transcribed by hand. Refuses to pass on
  an empty claim list.
- The corpus exclusion filter now reads Chinese. Its patterns use character
  classes covering both scripts and carry no optional dependency, so it cannot
  silently degrade to scanning English only.
- `guard` extra for running a local guard classifier, with `transformers` capped
  below 5 and both failure modes recorded in the comment beside the pin.

### Fixed
- **The source distribution is now an allowlist and cannot publish an untracked
  file.** `pyproject.toml` previously declared no sdist file selection, which is
  an exclude list that fails open: hatchling packaged the working tree minus the
  *repository's* `.gitignore`, and never reads a contributor's global gitignore.
  Anything hidden there is invisible to `git status`, to review and to CI, and is
  packaged anyway — permanently, since PyPI uploads cannot be unpublished.

  This was live, not theoretical. Built against the old configuration the sdist
  contained `data/.gitkeep` and `results/.gitkeep`, two files git does not track.
  Both are empty, so nothing escaped; the mechanism is the finding.
  `tests/unit/test_sdist_contents.py` now builds the sdist and fails if any
  member is untracked or credential-shaped — a check that needs no list of what
  local tooling happens to be called.
- **Every README link is absolute.** The README is the `long_description`, and
  PyPI resolves no relative target, so 18 of them were dead links or broken
  images on the published page — including `docs/results_matrix.png`, which is
  the figure the headline finding is delivered through, and `./LICENSE`, which is
  badge-wrapped and invisible to a scan that reads only the outermost link on a
  line. `tests/unit/test_readme_links.py` fails on any relative target, on an
  image served from a GitHub HTML page rather than `raw.githubusercontent.com`,
  and on an absolute link whose path is absent from the repository.
- Removed a module count from the README that had drifted from the actual figure.
  It was added after 0.3.0 shipped and never reached the published description,
  so no release carried it.

## [0.3.0] — 2026-07-16

Research-legibility, validation, and hardening since 0.2.1 — documentation,
tooling, and reproducibility only (no change to the core measurement API). This
is the public **freeze** release: a complete, honest, reproducible artifact whose
headline negative result is validated by a positive control.

### Added
- **Positive control** — a `llama2-uncensored-local` target
  (`configs/run_positive_control.yaml`) run through the identical
  run/score/cross-judge pipeline reports **80% ASR** (cross-judge κ = +0.935),
  demonstrating the harness registers a high attack-success rate on a vulnerable
  model. Documented in `METHODOLOGY.md` §12.5.
- **One-command headline repro** — `scripts/headline_table.py` regenerates the
  `METHODOLOGY.md` §8 table from cached run artifacts (no API calls); `--check`
  asserts every cell matches the frozen numbers.
- **`tests/README.md`** mapping each test suite to the claim it defends, plus a
  one-line `Defends:` header on every test module.
- Optional `num_ctx` on the Ollama target adapter (a bounded context window lets
  a 7B model load on an 8 GB-VRAM machine).
- `uv.lock` committed for a byte-for-byte reproducible environment.
- A README **pipeline diagram** ("how it fits together") and a **two-repo stack**
  pointer to the `agent-release-gates` companion + the project map.

### Changed
- **README** re-led around the research question and the negative/meta finding;
  the positioning / release-gate material moved into a lower "where this sits"
  section.
- **`METHODOLOGY.md`** gained a TL;DR/abstract and a consolidated **Threats to
  validity** section (detectable-effect bound, positive control, static-vs-adaptive
  scope); the benchmark-quality report card is now a paper-style write-up.
- Recruiter-oriented phrasing neutralised to a neutral reference voice; rounded
  out `[project.urls]` (Homepage / Documentation / Changelog) for the PyPI sidebar.

### Security
- Validate `--pack-id` as a safe single path segment (reject `../` traversal and
  absolute paths) at both the library and CLI boundary.
- Documented that Hugging Face datasets are loaded **data-only** (no remote code;
  `datasets` ≥ 4 has no `trust_remote_code`).
- Pinned all third-party GitHub Actions to full commit SHAs (supply-chain
  hardening), notably for the OIDC-privileged publish workflow.

### CI
- Coverage is computed (`--cov=src/redteam`) and gated with `--cov-fail-under=75`
  so it can't silently regress.

## [0.2.1] — 2026-07-04

Maintenance release: corrects the package author/copyright metadata (the first
publish carried the wrong author), adds automated releases, and rounds out the
community-health files.

### Added
- **Automated PyPI releases via Trusted Publishing** (`.github/workflows/publish.yml`)
  — publishing a GitHub Release builds and uploads to PyPI over OIDC, with no
  stored token; the job also verifies the tag matches the package version.
- Community-health files: `SECURITY.md` (private reporting for vulnerabilities
  and suspected exclusion-filter leaks), `CODE_OF_CONDUCT.md` (Contributor
  Covenant 2.1), GitHub issue forms + a PR template.

### Changed
- Corrected the package **author / copyright** metadata to `Cheng-Yuan King`
  (`rosscyking1115@gmail.com`) in `pyproject.toml`, `LICENSE`, and the README
  citation. The public **contact** address (`rosscyking@gmail.com`) in the
  security / conduct / disclosure lines is unchanged.
- The benchmark-quality scorecard datasets are now **pinned to commit SHAs**
  (`scripts/hf_scorecard.py`), so `docs/findings/benchmark-quality-report-card.md`
  reproduces exactly.

## [0.2.0] — 2026-07-02 — the adversarial benchmark foundry

Repositioned from a static red-team harness (`llm-redteam-harness`) into an
upstream **benchmark foundry** (`redteam-foundry`). The v1 measurement core is
unchanged; these are additive. First public release.

### Added
- **Corpus quality audit** (`redteam corpora audit`) — exact + near-duplicate
  detection including cross-source overlap, composition, prompt-length stats,
  and label-integrity checks, rendered as a quality report + data card.
- **Language + attack-family taxonomy** — script-based language/code-switching
  detection and heuristic attack-family surface markers, surfaced in the audit.
- **Benchmark staleness scoring** (`redteam corpora staleness`) — a transparent,
  component-broken-out heuristic composing corpus and run signals.
- **Benign control set + defence comparison** (`redteam compare-defences`,
  `redteam benign export`) — false-refusal rate and
  `safe_usefulness = (1 - ASR) * (1 - FRR)` per defence config.
- **Multilingual over-refusal** (`redteam frr-by-language`,
  `redteam benign export --multilingual`) — benign control set in
  zh-Hant / zh-Hans / ja / ko + code-switched, with per-language FRR.
- **Challenge-pack exporter** (`redteam export-pack`) — versioned packs
  (`pack.yaml` + `scenarios.jsonl` + `datacard.md`) with adversarial prompts
  redacted by default, plus a reader (`redteam.packs.read_challenge_pack`) and
  a downstream consumption contract (`examples/export_to_agent_release_gates.md`).
- **Audit any Hugging Face dataset** (`redteam corpora audit-hf --dataset ...
  --prompt-column ... [--revision ...]`) — not just the four built-in corpora;
  the safety exclusion filter runs first. New `source="external"` /
  `category="unknown"` schema values back it.
- **Cross-dataset benchmark-quality scorecard** (`scripts/hf_scorecard.py`) and a
  written finding (`docs/findings/benchmark-quality-report-card.md`) auditing four
  public jailbreak datasets: all English-only, roleplay-persona-dominant, and
  duplicated to varying degrees.
- `docs/ROADMAP.md`; committed real-data findings under `reports/samples/`.

### Fixed
- Exclusion-filter leaks (WMD "synthesis" noun, several self-harm phrasings,
  case-insensitive category gate) with regression tests.
- Budget guard now **reserves** its estimate so concurrent calls can't
  collectively exceed the per-run cap.
- Llama Guard fails **closed** on an empty/errored verdict.
- Spotlighting / SecAlign neutralise their own fence markers in untrusted input
  (closes a delimiter-injection bypass); SecAlign no longer passes messages
  through unfenced.
- OpenAI target fails loud without a pricing entry (no silent $0 budget bypass).
- Krippendorff's α finite-sample correction; `compute_kappa` blank-cell guard;
  cross-judge agreement reports `None` (not `0.0`) when not computable.

### Changed
- **Renamed the project/package to `redteam-foundry`** (was
  `llm-redteam-harness`). The `redteam` CLI command and `src/redteam/` module are
  unchanged — `pip install redteam-foundry` still gives you `redteam ...`.
- Default install slimmed: the unused dashboard deps (`streamlit`, `plotly`)
  moved to an opt-in `[dashboard]` extra. The audit / staleness / dedup path
  needs no API key.

## [0.1.0] — v1 measurement core

- Loaders for AdvBench, JailbreakBench, HarmBench, AgentDojo (commit-pinned) with
  a safety exclusion filter.
- Anthropic + Ollama targets (OpenAI stub); disk response cache; per-run and
  per-call budget guards.
- Six composable defences (system prompt, Constitutional, Spotlighting,
  SecAlign, Llama Guard 4 pre/post).
- Rule-based + LLM-judge scoring with an independent cross-judge; bootstrap
  confidence intervals; Cohen's κ and Krippendorff's α.
- UK AISI Inspect eval-log export.

[0.5.1]: https://github.com/rosscyking1115/redteam-foundry/releases/tag/v0.5.1
[0.5.0]: https://github.com/rosscyking1115/redteam-foundry/releases/tag/v0.5.0
[0.4.1]: https://github.com/rosscyking1115/redteam-foundry/releases/tag/v0.4.1
[0.4.0]: https://github.com/rosscyking1115/redteam-foundry/releases/tag/v0.4.0
[0.3.0]: https://github.com/rosscyking1115/redteam-foundry/releases/tag/v0.3.0
[0.2.1]: https://github.com/rosscyking1115/redteam-foundry/releases/tag/v0.2.1
[0.2.0]: https://github.com/rosscyking1115/redteam-foundry/releases/tag/v0.2.0
[0.1.0]: https://github.com/rosscyking1115/redteam-foundry/releases/tag/v0.1.0
