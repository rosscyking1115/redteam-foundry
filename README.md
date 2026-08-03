# redteam-foundry

A measurement harness for checking whether the standard tests used to probe AI
language models for unsafe behaviour still tell you anything.

[![PyPI](https://img.shields.io/pypi/v/redteam-foundry.svg)](https://pypi.org/project/redteam-foundry/)
[![CI](https://github.com/rosscyking1115/redteam-foundry/actions/workflows/ci.yml/badge.svg)](https://github.com/rosscyking1115/redteam-foundry/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/rosscyking1115/redteam-foundry/blob/main/LICENSE)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/release/python-3130/)
[![Checked with mypy --strict](https://img.shields.io/badge/mypy-strict-2a6db2.svg)](https://mypy-lang.org/)

**The question.** Safety teams reach for a handful of published collections of
attack prompts to decide whether a model is holding up. Those collections are
years old and the models are not. Do they still separate a robust model from a
weak one — and how much should you trust the answer?

**The answer, in one line.** Mostly they do not: across every configuration
tested, the published attacks almost never succeed (0–4%), and a deliberately
paranoid set of defences does not measurably change that.

![Attack success rate across all 12 evaluation cells — point estimate with 95% bootstrap confidence interval. Ten of the twelve cells sit at 0%; the two non-zero cells are the AdvBench Llama baseline at 1% and the AgentDojo Llama baseline at 4%.](https://raw.githubusercontent.com/rosscyking1115/redteam-foundry/main/docs/results_matrix.png)

> **Status: active — the package is maintained, the research has reported.** All
> roadmap phases are done and both research lines have concluded; the headline
> result is frozen. This measures whether *benchmarks* still discriminate. It
> does not certify any model as safe, and it is not a security audit.

```bash
pipx install redteam-foundry && redteam --help
```

## What this is for

For anyone who has to decide whether a safety evaluation is still worth running:
model evaluation teams, safety researchers, and engineers who inherited a
benchmark suite and do not know whether a green result means the model is strong
or the test is worn out. The problem it solves is that **those two look
identical** — a robust model and an exhausted benchmark both report "0% of
attacks succeeded", and the success rate alone cannot tell them apart.

Existing tooling runs the attacks. This one asks whether running them still
tells you anything, and reports how much to trust its own answer. It is the
research half of a two-part stack: the companion project
[agent-release-gates](https://github.com/rosscyking1115/agent-release-gates)
consumes the challenge packs exported here and makes the ship/warn/block call.
**Validate the benchmark before you trust the gate.** Release decisions are
deliberately out of scope here.

## What the result means

That near-zero is a statement about the benchmarks as much as the models.
Instruction tuning has largely *saturated* the static, published jailbreak and
prompt-injection corpora the field still reaches for as a safety signal. They no
longer discriminate.

The contribution is not a new attack. It is a reproducible, judge-validated
measurement that these benchmarks have stopped discriminating, plus the tooling
to quantify why. It is a meta-science result about benchmark validity, not a
claim that any model is safe. What the benchmarks *under*-measure — the live
agentic tool-use loop, multi-turn attacks, adaptive optimisation — is named in
[§ Threats to validity](https://github.com/rosscyking1115/redteam-foundry/blob/main/METHODOLOGY.md#12-threats-to-validity),
not hidden.

## Why the result is trustworthy, not just low

A near-zero number is easy to report and easy to distrust.

- **A positive control rules out "the harness just under-elicits".** Through the
  *identical* pipeline, a known-vulnerable model scores 80% (cross-judge 80.6%,
  κ = +0.935). The apparatus registers a high attack-success rate when the target
  really is vulnerable, so the 0–4% is a property of the aligned models.
- **Two judges, and honesty about when they agree.** Every verdict is scored and
  re-scored independently. Where labels actually vary the judges agree strongly
  (κ = +0.935, n = 98). The 12 matrix cells also report κ = +1.000, but in 11 of
  them both judges labelled every case identically, which makes κ an undefined
  `0/0` rather than evidence — the repository says so, and a check enforces it.
- **Confidence intervals at honest sample sizes.** Percentile-bootstrap, not CLT
  intervals, which under-cover at n≈50–100. With n = 100 and zero successes the
  detectable-effect bound is [0, 3.6%], stated rather than glossed.
- **Pinned and deterministic.** Dated model versions, datasets pinned to upstream
  commits, every API call cached, so re-runs are free and reproduce exactly.
- **Scoped, with threats to validity written down.** Single-turn only; static
  published prompts, not adaptive attacks.

One consequence is worth stating plainly: this reports attack-success rate and
**not** refusal rate. The cross-judge layer found refusal is not well-posed —
an indirect-injection task has two things that can be refused, so the judges
disagree, sometimes worse than chance. Refusal is reported as a descriptive
signal of response style, never as a safety metric.

## Ethics

> [!IMPORTANT]
> This project uses only published adversarial prompts and does not generate
> novel jailbreaks in any language. Excluded categories (CSAM,
> weapons-of-mass-destruction synthesis, detailed self-harm methods) are filtered
> at corpus-load time and verified by a CI test. Results are aggregate; exported
> adversarial prompts are redacted. The multilingual work is benign-only. Full
> policy in [`ETHICS.md`](https://github.com/rosscyking1115/redteam-foundry/blob/main/ETHICS.md).

If you are a model provider whose model is included and want example transcripts
removed, email rosscyking@gmail.com and I will remove them within 24 hours.

## Documentation

| Document | What is in it |
| --- | --- |
| [Getting started](https://github.com/rosscyking1115/redteam-foundry/blob/main/docs/getting-started.md) | Install, development setup, reproducing the headline table |
| [Command reference](https://github.com/rosscyking1115/redteam-foundry/blob/main/docs/commands.md) | Every sub-command, offline and live, and how the stages fit together |
| [**Finding: are jailbreak benchmarks still worth running?**](https://github.com/rosscyking1115/redteam-foundry/blob/main/docs/findings/benchmark-quality-report-card.md) | The paper-style write-up: question, method, results with CIs, threats to validity, related work |
| [**Finding: what does this metric return when nothing happened?**](https://github.com/rosscyking1115/redteam-foundry/blob/main/docs/findings/what-does-this-metric-return-when-nothing-happened.md) | A running catalogue of metrics and checks in this repository that were satisfied by the *absence* of the thing they measured — several introduced while fixing the previous one |
| [**Finding: a preregistered null at p = 0.0001**](https://github.com/rosscyking1115/redteam-foundry/blob/main/docs/findings/a-preregistered-null-at-p-0-0001.md) | A real, highly significant effect reported as null because it missed an effect-size bar fixed before the run |
| [**Finding: what mechanical conversion does to Taiwan-native safety text**](https://github.com/rosscyking1115/redteam-foundry/blob/main/docs/findings/what-mechanical-conversion-does-to-taiwan-native-safety-text.md) | Converting 400 Taiwan-native safety prompts to Simplified and back changes 66% of them |
| [`METHODOLOGY.md`](https://github.com/rosscyking1115/redteam-foundry/blob/main/METHODOLOGY.md) | Source of truth for every reported number; metric validation; threats to validity |
| [`ETHICS.md`](https://github.com/rosscyking1115/redteam-foundry/blob/main/ETHICS.md) | Excluded categories, redaction, disclosure, provider terms |
| [`tests/README.md`](https://github.com/rosscyking1115/redteam-foundry/blob/main/tests/README.md) | Which claim each test suite defends |
| [`docs/ROADMAP.md`](https://github.com/rosscyking1115/redteam-foundry/blob/main/docs/ROADMAP.md) | The foundry pivot, phase status, follow-up hardening |
| [`docs/RELEASING.md`](https://github.com/rosscyking1115/redteam-foundry/blob/main/docs/RELEASING.md) | How a release is cut, and what the release path refuses to publish |
| [`CONTRIBUTING.md`](https://github.com/rosscyking1115/redteam-foundry/blob/main/CONTRIBUTING.md) | Scope, dev setup, ethics rules for adding corpora |
| [`CHANGELOG.md`](https://github.com/rosscyking1115/redteam-foundry/blob/main/CHANGELOG.md) | Release history |
| [`reports/samples/`](https://github.com/rosscyking1115/redteam-foundry/tree/main/reports/samples/) | Committed real-data findings: staleness, defence comparison, data card |

Two scoping documents record work considered and **not** built:
[porting the AgentDojo cell to a native Inspect task](https://github.com/rosscyking1115/redteam-foundry/blob/main/docs/inspect-evals-port-scoping.md)
and [a gap analysis toward an arXiv preprint](https://github.com/rosscyking1115/redteam-foundry/blob/main/docs/preprint-scoping.md).

## Citation

```bibtex
@software{redteam_foundry_2026,
  title  = {redteam-foundry: An adversarial benchmark foundry for LLM safety},
  author = {Cheng-Yuan King},
  year   = {2026},
  url    = {https://github.com/rosscyking1115/redteam-foundry}
}
```

## Licence

MIT — see [`LICENSE`](https://github.com/rosscyking1115/redteam-foundry/blob/main/LICENSE).
