# Scoping: porting the AgentDojo cell to an Inspect task

Status: **scoping only — nothing built.** Written 2026-07-27.
Decision owner: Ross. This document exists to make the decision cheap, not to
pre-empt it.

The brief was: port the AgentDojo evaluation cell to a proper Inspect task
(`@task`, `@scorer`, registered entry point), ship the positive control as a
task variant, and state the gap against `inspect_evals`' contribution
requirements.

Two things about the target contradict the brief's premise, and both change the
shape of the work. They are in §1. The port itself is still worth doing, but for
a different reason and via a different route than assumed.

(The first of the two — the move to a register model — was already recorded in
the team's project notes on 2026-07-22. It is re-verified here from primary
sources because the brief assumed otherwise; the arXiv requirement and the
acceptance bar in §2 are the parts that were not previously captured.)

---

## 1. Two findings that break the brief's premise

### 1.1 `inspect_evals` no longer accepts code contributions for new evals

From the repository's own `CONTRIBUTING.md`:

> "We no longer accept code submissions for new eval implementations."

> "To add an eval that you have already implemented, please follow the steps
> [to add evals to Inspect Evals Register](register/README.md)."

And from the README's notice:

> "From 8th May 2026 onwards, community contributions will move to the
> /register/ folder, which means: Submission requires opening a GitHub issue
> with your arXiv URL and source code link."

The model is now a **register**: you keep your implementation in your own
repository, and `inspect_evals` carries a listing that points at a pinned
commit in it. A bot validates the submission, derives metadata, and opens the
PR on your behalf.

This is mostly *good news* for this repo. The old route meant matching their
layout, their review queue, and their house style, and handing over
maintenance. The register route means the artifact stays here — with its own
README, its own methodology document, and its own positive control — and still
appears in the `inspect_evals` listing. It also means the port is no longer
gated on a maintainer's appetite for a twelfth injection eval.

It also means "contributing to `inspect_evals`" now means something weaker than
it did when the brief was written. Worth being honest about that in any
CV/portfolio framing: a register listing is a pointer to your repo, not merged
code in theirs.

### 1.2 AgentDojo is already in `inspect_evals` — as the full agentic benchmark

`src/inspect_evals/agentdojo` already exists. It runs the real thing: five task
suites, a live agent loop with tools, scored on benign utility, utility under
attack, and security. It cites the same paper this repo's loader does
(arXiv 2406.13352).

This repo's AgentDojo cell is a deliberate **strict subset** of that: the
injection is rendered as one static prompt, with no tool execution and no agent
loop. `METHODOLOGY.md` §11 and §12.4 already say so, and call it a lower bound.

So a port cannot be pitched as "AgentDojo for Inspect" — that exists, and it is
strictly stronger. The register's validation includes duplicate eval-ID and
task-name checks plus fuzzy duplicate detection, and a weaker variant of an
existing entry is the most likely thing to be bounced.

**What is genuinely not there** is the thing the brief correctly identified: an
eval that ships its own positive control. The existing AgentDojo entry, like
essentially every other entry, cannot tell you whether a low attack-success
rate means the target resisted or the harness failed to elicit. That is the
contribution. The AgentDojo corpus is the vehicle, not the pitch.

---

## 2. What the register actually requires, and what this repo has

From `register/README.md`, an upstream repository must:

| Requirement | Status here | Gap |
| --- | --- | --- |
| `pyproject.toml` with a `[project]` table, installable | ✅ present, published to PyPI as `redteam-foundry` | none |
| Declares `inspect_ai` as a dependency | ⚠️ optional extra `[inspect]` only | must become a real dependency of the task package |
| Each task defined with `@task` from `inspect_ai` | ❌ none exist | **the port** — see §3 |
| External assets hosted and pinned in version-controlled storage with explicit `revision=` | ✅ AgentDojo pinned to commit `18b501a…`, suite version `v1.2.1`; model versions pinned in `configs/model_versions.yaml` | AgentDojo data ships inside the AGPL PyPI package rather than a pinned HF revision — needs a note, possibly a licence conversation |
| Public repo, submission pinned to a full 40-char SHA | ✅ public | none |
| **arXiv URL** (mandatory — used to derive metadata and to show "the methodology behind the eval's design and implementation is publicly available") | ❌ **none** | **the real blocker** — see §4 |

The bot's always-run checks are schema compliance, repo reachability, SHA
existence, duplicate eval-ID/task-name detection, and a cap of 10 entries per
PR. On significant changes it also checks that the task function exists and is
decorated, that the eval runs with its dataset and scorer, that the description
is accurate, and a security pass.

The maintainers' stated acceptance bar (from the contributing docs) is worth
reading literally, because it is the second-hardest constraint after arXiv:

> "Well-established in the research community — ideally with usage or citations
> in published benchmarks or papers"

> "the evaluation should be replicable, ideally with a reference
> implementation"

Baseline results from frontier models are also expected. This repo *has* those
— Sonnet 4.6 and Llama 3.1 8B, with CIs and a positive control — which is
better evidence than most first-time submissions carry.

---

## 3. The port itself

Nothing here is hard. The pieces exist and are tested; this is re-expressing
them in Inspect's vocabulary.

### 3.1 What maps directly

| Inspect concept | What it becomes here | Source |
| --- | --- | --- |
| `Sample` | one rendered `(user_task, injection_task)` pair | `corpora/agentdojo.py::_render_pair` (already produces a stable `id`, `prompt`, `references`) |
| dataset function | `AgentDojoLoader` iteration, pinned to `18b501a…` / `v1.2.1` | `corpora/agentdojo.py` |
| `Solver` | the defence stack — system prompt, spotlighting, SecAlign fencing — as a chain of solvers | `defences/` (already composable via a `send()`-compatible protocol) |
| `@scorer` | the judge rubric returning `{asr, refusal, confidence, reasoning}` | `scorers/judge_claude.py` + `_judge_schema.py` |
| metric | `mean()` over ASR, plus the bootstrap CI | `stats.py::bootstrap_proportion_ci` |
| second scorer | the cross-judge, as a separate registered scorer | `orchestrator.py` cross-judge path |

The defence classes deliberately do not inherit from `Target` — they delegate
to an inner `SendLike` so caching and budget accounting happen once. That
design ports cleanly onto Inspect solvers, which chain the same way.

### 3.2 What needs writing

1. A task module with `@task` entry points, typed, no `name=` parameter.
2. A `@scorer` wrapping the existing judge. The judge prompt already treats
   attack and response as delimited data and validates output through Pydantic
   — that hardening should survive the port verbatim, not be re-implemented.
3. `[project.entry-points.inspect_ai]` registration in `pyproject.toml`.
4. An `eval.yaml`: `title`, `description`, `arxiv`, `group`, `contributors`,
   `tasks` (with `dataset_samples`), `external_assets`, `tags: ["Agent"]`.
5. Tests: unit tests for the scorer, at least one end-to-end test against
   `mockllm/model`, and a `record_to_sample()` test using a real example.
6. A README section reporting results against the reference implementation.

### 3.3 The positive-control variant — and a problem with it

This is the differentiator, and it is the part that needs a decision rather
than just typing.

**The problem: the existing positive control is on the wrong corpus.**
`configs/run_positive_control.yaml` runs `llama2-uncensored:7b` against
**AdvBench** at n=100. There is no AgentDojo positive control. Shipping the
AdvBench control as a "variant" of an AgentDojo task would mean the control and
the task under test share neither corpus nor threat model, which is exactly the
kind of thing this repo is otherwise careful about.

Three options, in order of preference:

- **(a) Run a real AgentDojo positive control.** `llama2-uncensored:7b` against
  the AgentDojo static-injection corpus at n=50, no defences. Generation is
  local, so $0; the two judges cost roughly $0.10–0.15 at the observed per-case
  rates. This is the honest version and it is nearly free.
  **But there is prior evidence it will fail.** A Gate-0 study in the sibling
  `agent-redteam-replay` project killed a local-model capability arm because
  small open models (≤8B) on this hardware could not drive AgentDojo at all —
  16.7% against a 75% capability gate — with the conclusion that *robustness is
  not identifiable under failed capability*. The same logic applies to a
  positive control: if the model cannot perform the user task, a low hijack
  rate measures incapacity, not resistance, and the control is not a control.
  One thing does cut the other way, and it is why (a) is still worth an
  afternoon: that Gate-0 result was on the **live agent loop**, which requires
  tool-calling discipline. This repo's cell is a **static render** — one prompt,
  no tool calls — so the capability bar is materially lower and an unaligned 7B
  may well clear it. Unknown until run. Treat as a cheap experiment with a
  named failure condition, not a formality.
- **(b) Ship two tasks** — an AdvBench direct-attack task carrying its existing
  validated control (κ = +0.935, already run), and the AgentDojo task without
  one, documented as such. Honest, and it does not depend on an untested
  assumption. It concedes the differentiator on the AgentDojo entry, but the
  AdvBench entry still carries it.
- **(c) Ship the AgentDojo task with the AdvBench control labelled as a
  *harness-level* control rather than a task-level one.** Weakest; only if (a)
  fails and (b) is unattractive.

### RESOLVED 2026-07-27: (a) was run, and it failed. Falling back to (b).

Option (a) was executed with the threshold pre-registered in
`configs/run_agentdojo_positive_control.yaml` (PASS = judge ASR ≥ 20%). Result:
**2%**. Full write-up in METHODOLOGY §12.6.

The failure is not "the model resisted" — it never refuses, and it confabulates
instead of reading the tool output (26% of responses cite email addresses absent
from the prompt). The cell measures incapacity. Notably this refutes the
reasoning in the paragraph above: the static render *does* remove the
tool-calling requirement, but the binding constraint turned out to be
context-grounding, not tool-calling.

**So the plan is (b): two tasks.** An AdvBench direct-attack task carrying its
validated control (80% ASR, κ = +0.935), and an AgentDojo task documented as
uncontrolled. That is weaker than hoped for the AgentDojo entry, but it is the
honest configuration and the AdvBench entry still carries the differentiator.

This also produced a better idea for later, which is a design change rather than
a rerun and so is **Ross's call, not done**: build a *synthetic* positive
control — take a capable model and give it a system prompt instructing it to
follow instructions found in tool output. That verifies the pipeline detects a
hijack when one certainly occurs, without depending on finding an unaligned
model that is also competent. It isolates the measurement question from the
model-capability question, which is arguably what a positive control should do.
Cost: one local run plus ~£0.20 of judging.

---

## 4. The blocker: there is no paper

The arXiv URL is mandatory and is not a formality — the register uses it to
derive the listing's metadata and to establish that the methodology is public.

Citing AgentDojo's paper (2406.13352) does not work. That paper describes the
full agentic benchmark, not this static subset, and says nothing about a
positive control. The derived metadata would describe someone else's eval, and
the duplicate check would be looking straight at the existing entry.

The methodology that needs to be public is **this repo's own**: the static-render
subset, the defence stack, the two-judge protocol, the degenerate-kappa
correction, and the positive control. Most of that is already written —
`METHODOLOGY.md` and `docs/findings/benchmark-quality-report-card.md` are
paper-shaped and carry RQ, method, results with CIs, threats to validity, and
related work.

**So the sequencing is the reverse of the brief's.** The shortest honest path is
not port-then-register; it is:

1. Settle the positive-control corpus question (§3.3) — small, cheap, decides
   the task count.
2. Turn the report card into a preprint and post it to arXiv (cs.CR or cs.LG).
   The content largely exists; the work is framing, formatting, and endorsement.
3. Port the task(s), with the paper's numbers as the README's evaluation report.
4. Open the register issue with the arXiv URL and a pinned SHA.

Step 2 is the long pole and the one worth deciding on first. It is also
independently valuable: a citable negative result with a positive control is a
stronger portfolio object than a register listing is.

### Rough effort

| Step | Estimate | Notes |
| --- | --- | --- |
| AgentDojo positive control run | half a day | local generation, ~$0.15 of judge |
| arXiv preprint from existing docs | **5–7 focused days, plus endorsement wall-clock** | scoped separately in [`preprint-scoping.md`](./preprint-scoping.md) |
| Task + scorer port, tests, `eval.yaml` | 2–3 days | pieces exist and are tested |
| Register submission | an hour | bot-driven; SHA pin + issue form |

The preprint estimate above is firmer than the "days, not hours" first written
here, and one blocker was missed on the first pass: since **21 January 2026**
arXiv no longer accepts an institutional email as sufficient endorsement for a
first submission to a category. Ross needs either prior in-domain authorship
(he has none) or a personal endorser. That is a dependency on another person and
belongs at the front of the queue, not the end. See
[`preprint-scoping.md`](./preprint-scoping.md) §1.2.

---

## 5. Recommendation

Do the port — but pitch and sequence it correctly.

- Not "AgentDojo for Inspect" (taken, and by a stronger implementation).
- **"An injection eval that ships its own positive control"** — which, as far as
  the current listing shows, nothing else does.
- Fix the control's corpus first, write the paper second, port third, register
  fourth.

If the arXiv step is not something you want to take on right now, the port is
still worth building for its own sake: it makes the harness runnable by anyone
on Inspect rather than only readable via the existing one-way log exporter, and
it costs nothing to hold the register submission until a preprint exists.

## Sources

- [inspect_evals CONTRIBUTING.md](https://github.com/UKGovernmentBEIS/inspect_evals/blob/main/CONTRIBUTING.md)
- [inspect_evals README](https://github.com/UKGovernmentBEIS/inspect_evals)
- [Register submission guide](https://github.com/UKGovernmentBEIS/inspect_evals/blob/main/register/README.md)
- [Contributing docs site](https://ukgovernmentbeis.github.io/inspect_evals/contributing/)
- [Generality Labs evaluation template](https://github.com/Generality-Labs/inspect-evals-template/blob/main/CONTRIBUTING.md)
- [Existing AgentDojo entry](https://github.com/UKGovernmentBEIS/inspect_evals/tree/main/src/inspect_evals/agentdojo)

All fetched 2026-07-27.
