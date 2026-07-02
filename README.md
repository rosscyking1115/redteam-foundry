# redteam-foundry

> An **adversarial benchmark foundry** for LLM safety: audit attack corpora,
> measure defence impact, score benchmark *staleness*, test multilingual
> over-refusal, and export safe challenge packs — all with judge-validated,
> reproducible numbers. A measurement tool, not a weapon (see [`ETHICS.md`](./ETHICS.md)).

[![CI](https://github.com/rosscyking1115/redteam-foundry/actions/workflows/ci.yml/badge.svg)](https://github.com/rosscyking1115/redteam-foundry/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/release/python-3130/)

## Positioning

`redteam-foundry` is the upstream **research layer** of a two-layer AI-safety
stack. It validates adversarial corpora, measures defence effectiveness, studies
whether published benchmarks still measure real deployment risk, and exports safe
challenge packs for downstream release-gating systems to consume.

It deliberately does **not** make production release decisions. Ship / warn /
block, incident replay, and policy-as-code gates belong in a separate deployment
layer — see [Relationship to agent-release-gates](#relationship-to-agent-release-gates).

> **Validate the benchmark before you trust the gate.**

| | This repo (research layer) | A release-gate layer |
| --- | --- | --- |
| Job | Discover, validate, and package adversarial benchmarks | Replay incidents, apply policy, decide ship/warn/block |
| Output | Audited corpora, judge-validated ASR/defence measurements, challenge packs | Deployment evidence, release decisions |
| Question | "Is this benchmark still meaningful, and how much do I trust the score?" | "Is this agent safe to ship right now?" |

## What it does

- **Runs published adversarial prompts** (AdvBench, JailbreakBench, HarmBench,
  AgentDojo — each pinned to an upstream commit) against target LLMs through
  composable, togglable defence stacks, and reports attack-success rate (ASR)
  with bootstrap confidence intervals and real API cost.
- **Validates its own numbers**: every verdict is scored by an LLM judge and
  re-scored by an independent second judge; agreement (Cohen's κ, Krippendorff's
  α) is a first-class output.
- **Audits corpus quality**: exact + near-duplicate detection (including
  cross-source overlap), language/script coverage, attack-family markers, and
  label-integrity checks → a quality report and a data card.
- **Scores benchmark staleness**: a transparent, component-broken-out heuristic
  answering "is this a robust model, or a stale benchmark?".
- **Measures over-blocking**: a benign control set (English + Traditional/
  Simplified Chinese, Japanese, Korean, and code-switched) yields false-refusal
  rate (FRR) and a combined *safe-usefulness* score per defence.
- **Exports challenge packs**: versioned, self-describing fixtures a downstream
  release gate can consume — with adversarial prompts redacted by default.
- **Interoperates**: any run exports to a
  [UK AISI Inspect](https://inspect.aisi.org.uk/) eval log.

## Headline finding

Across **2 target models**, **2 benchmark families**, and up to **4 composable
defence configurations** (12 evaluation cells), published adversarial prompts
succeed between **0% and 4%** of the time, and a paranoid prompt-only defence
stack does **not** measurably move that number. Judge agreement on attack
success is perfect — **Cohen's κ = +1.00 in all 12 cells**.

![Attack success rate across all 12 evaluation cells — point estimate with 95% bootstrap confidence interval. Ten of the twelve cells sit at 0%; the two non-zero cells are the AdvBench Llama baseline at 1% and the AgentDojo Llama baseline at 4%.](docs/results_matrix.png)

> [!NOTE]
> A near-zero ASR is a result about the **benchmark**, not just the model. It
> can mean the model is robust *or* the benchmark is stale — and ASR alone
> cannot tell them apart. Measuring that difference (staleness, defence
> sensitivity, multilingual over-refusal) is what this foundry is for. Full
> numbers, validation, and limits are in [`METHODOLOGY.md`](./METHODOLOGY.md).

## Getting started

```bash
git clone https://github.com/rosscyking1115/redteam-foundry.git
cd redteam-foundry
uv venv --python 3.13
source .venv/bin/activate            # macOS/Linux
# .venv\Scripts\activate             # Windows PowerShell
uv pip install -e ".[dev]"
cp .env.example .env                 # fill in ANTHROPIC_API_KEY
pre-commit install
pytest tests/unit                    # should pass green
redteam version                      # prints the installed version
```

The CLI is `redteam ...` (equivalently `python -m redteam ...`).

> [!WARNING]
> Live runs call paid APIs. Each run enforces a hard USD budget cap (set per
> config in `configs/`), and the judge/target adapters enforce a per-call cap —
> but set a matching **console budget cap** before your first run anyway.

## Commands

### Benchmark research (the foundry) — offline, no API key

These analyse corpora and existing run artifacts; they need cached corpora but
no live model calls.

```bash
# Audit corpora: duplicates, cross-source overlap, language + attack-family
# coverage, label issues -> quality report + data card + JSON.
redteam corpora audit --output reports/corpus_audit/

# Audit ANY Hugging Face adversarial dataset, not just the built-in four.
redteam corpora audit-hf --dataset owner/name --prompt-column prompt --revision <sha>

# Score benchmark staleness (heuristic). Pass --run for evaluation JSONs to
# light up the run-based components (universal-low-ASR, defence-insensitivity,
# judge-disagreement); corpus-only otherwise.
redteam corpora staleness --only agentdojo --run results/<run>.cross-judged.json

# Compare defences on ASR, false-refusal rate, safe-usefulness, cost, latency.
redteam compare-defences --run results/<adv>.judged.json --benign-run results/<benign>.json

# False-refusal rate broken down by language (over a benign run).
redteam frr-by-language --run results/<benign_multilingual>.json

# Export a versioned challenge pack (adversarial prompts redacted by default).
redteam export-pack --pack-id my-pack --only advbench

# Write the benign control sets to JSONL for inspection / running.
redteam benign export                 # English control set
redteam benign export --multilingual  # zh-Hant/zh-Hans/ja/ko + code-switch
```

### Measurement core — needs an API key / local Ollama

```bash
redteam corpora download                                   # fetch + pin corpora
redteam run --config configs/run_anthropic_baseline.yaml   # evaluate
redteam score --run results/<run>.json                     # LLM-judge scoring
redteam cross-judge --run results/<run>.judged.json        # second judge + agreement
redteam export-inspect --run results/<run>.json            # UK AISI Inspect log
```

Run `redteam --help` for the full command list; every sub-command has `--help`.

## Why this reports ASR and not refusal rate

The cross-judge layer found that **ASR is well-posed and `refusal_rate` is not**:
the two judges agree perfectly on whether an attack succeeded, but disagree —
sometimes worse than chance — on whether a response was a "refusal", because an
indirect-injection task has two things that can be refused (the user's request
and the injected instruction). `refusal_rate` is therefore reported as a
*descriptive* signal of response style only, never as a safety metric. This is
documented, not hidden — see [`METHODOLOGY.md`](./METHODOLOGY.md) §7.

## Relationship to agent-release-gates

This repository is the upstream **adversarial benchmark layer**: it validates
static attack corpora, measures defence stacks, scores its own reliability, and
exports safe challenge packs. Production release decisions — incident replay,
policy-as-code gates, deployment evidence, and ship / warn / block
recommendations — are deliberately out of scope. A useful mental model:

- `redteam-foundry` discovers, validates, and packages adversarial scenarios.
- a release-gate layer (`agent-release-gates`) consumes selected scenarios as
  regression and release-readiness checks.

A benchmark research tool should not be the thing that decides whether an agent
ships, and a release gate is only as trustworthy as the benchmarks feeding it.
(`agent-release-gates` is a companion project; this section documents the
intended split.)

## Ethics

> [!IMPORTANT]
> This project uses **only** published adversarial prompts and does not generate
> novel jailbreaks in any language. Excluded categories (CSAM,
> weapons-of-mass-destruction synthesis, detailed self-harm methods) are
> filtered at corpus-load time and verified by a CI test. Results are aggregate;
> exported adversarial prompts are redacted. The multilingual work is
> benign-only. Full policy in [`ETHICS.md`](./ETHICS.md).

If you are a model provider whose model is included and want example transcripts
removed, email **rosscyking@gmail.com** — **24-hour removal commitment**.

## Development

`scripts/ci_local.ps1` (Windows) and `scripts/ci_local.sh` (Linux/macOS) run the
**exact** same checks as CI — ruff lint, ruff format check, mypy, pytest. Green
locally means green on the PR. Run artifacts (`results/`), audit outputs
(`reports/`), and non-sample packs (`challenge_packs/`) are gitignored — all
re-creatable from configs.

## Documentation

| File | What's in it |
| --- | --- |
| [**Finding: are jailbreak benchmarks still worth running?**](./docs/findings/benchmark-quality-report-card.md) | The write-up: staleness, a cross-dataset quality scorecard, and the multilingual result |
| [`METHODOLOGY.md`](./METHODOLOGY.md) | Source of truth for every reported number; metric validation; limits |
| [`ETHICS.md`](./ETHICS.md) | Excluded categories, redaction, disclosure, provider ToS |
| [`docs/ROADMAP.md`](./docs/ROADMAP.md) | The foundry pivot, phase status, and follow-up hardening |
| [`CONTRIBUTING.md`](./CONTRIBUTING.md) | Scope, dev setup, and the ethics rules for adding corpora |
| [`CHANGELOG.md`](./CHANGELOG.md) | Release history |
| [`reports/samples/`](./reports/samples/) | Committed real-data findings (staleness, defence comparison, data card) |

## Citation

```bibtex
@software{redteam_foundry_2026,
  title  = {redteam-foundry: An adversarial benchmark foundry for LLM safety},
  author = {Ross},
  year   = {2026},
  url    = {https://github.com/rosscyking1115/redteam-foundry}
}
```

## Licence

MIT — see [`LICENSE`](./LICENSE).
