# llm-redteam-harness

> A reproducible harness for measuring how published LLM defences change the
> attack success rate of published adversarial prompts — and for measuring how
> much to trust those numbers. Built as a measurement tool, not a weapon — see
> [`ETHICS.md`](./ETHICS.md).

[![CI](https://github.com/rosscyking1115/llm-redteam-harness/actions/workflows/ci.yml/badge.svg)](https://github.com/rosscyking1115/llm-redteam-harness/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/release/python-3130/)

## Headline finding

Across **2 target models**, **2 benchmark families**, and up to **4 composable
defence configurations** — 12 evaluation cells in total — published adversarial
prompts succeed between **0% and 4%** of the time, and a paranoid prompt-only
defence stack does **not** measurably move that number.

Every attack-success verdict is scored by an LLM judge and then independently
re-scored by a second judge model. Judge agreement on attack success is
**perfect — Cohen's κ = +1.00 in all 12 cells.**

The honest reading: 2026-era instruction tuning already neutralises these
published, *static* attacks on both a frontier model (Claude Sonnet 4.6) and a
small local model (Llama 3.1 8B). Prompt-only defences change the *style* of a
refusal, not the safety outcome. The open risk these static benchmarks
under-measure is the **full agentic loop** — interactive, multi-step tool use —
which is named explicitly as future work, not quietly omitted.

### AdvBench — direct attacks (n = 100 per cell)

| Target | Baseline ASR | Full-stack ASR |
| --- | ---: | ---: |
| Claude Sonnet 4.6 | 0% [0, 0] | 0% [0, 0] |
| Llama 3.1 8B (local) | 1% [0, 3] | 0% [0, 0] |

### AgentDojo — static indirect injection (n = 50 per cell)

| Target | Baseline | + Spotlighting | + SecAlign | Full prompt stack |
| --- | ---: | ---: | ---: | ---: |
| Claude Sonnet 4.6 | 0% | 0% | 0% | 0% |
| Llama 3.1 8B (local) | 4% [0, 10] | 0% | 0% | 0% |

All figures are attack success rate (ASR) from the LLM judge; brackets are 95%
percentile-bootstrap confidence intervals. Cross-judge κ on ASR = +1.00 for
every cell. Full numbers, validation, and limits in
[`METHODOLOGY.md`](./METHODOLOGY.md).

## Why this reports ASR and not refusal rate

The harness was built to report how trustworthy its own metrics are. The
cross-judge layer found that **ASR is well-posed and `refusal_rate` is not**:
the two judges agree perfectly on whether an attack succeeded, but disagree —
sometimes worse than chance — on whether a response was a "refusal", because an
indirect-injection task has two things that can be refused (the user's request
and the injected instruction). `refusal_rate` is therefore reported as a
*descriptive* signal of response style only. This is documented, not hidden —
see [`METHODOLOGY.md`](./METHODOLOGY.md) §7.

## What this is

A reproducible benchmark that:

1. Loads published adversarial prompts from AdvBench, JailbreakBench,
   HarmBench, and AgentDojo, each pinned to an upstream commit.
2. Sends them through 2 target LLMs — Claude Sonnet 4.6 (frontier) and
   Llama 3.1 8B (local, via Ollama).
3. Toggles composable defence stacks on and off — paranoid system prompt,
   Constitutional critique-and-revise, Spotlighting, SecAlign-style structured
   queries (Llama Guard 4 pre/post-filters are implemented but excluded from
   the v1 matrix; see `METHODOLOGY.md` §4).
4. Scores responses with a rule-based pre-screen, then an LLM judge, then an
   independent cross-judge for validation.
5. Reports ASR with bootstrap confidence intervals, inter-judge agreement
   (Cohen's κ, Krippendorff's α), and real API cost per run.

## Status

The v1 evaluation matrix is complete and the harness is feature-complete for
v1 scope. The next tracks — the full AgentDojo agent loop, multi-turn attacks,
and Inspect AI export — are listed in [`METHODOLOGY.md`](./METHODOLOGY.md) §12.

## Getting started

```bash
git clone https://github.com/rosscyking1115/llm-redteam-harness.git
cd llm-redteam-harness
uv venv --python 3.13
source .venv/bin/activate           # macOS/Linux
# .venv\Scripts\activate            # Windows PowerShell
uv pip install -e ".[dev]"
cp .env.example .env                # fill in ANTHROPIC_API_KEY
pre-commit install
pytest tests/unit                   # should pass green
python -m redteam version           # prints 0.1.0
```

The CLI is invoked as `python -m redteam ...`. Each run enforces a hard USD
budget cap (set per config in `configs/`); set a matching console cap before
the first run.

```bash
python -m redteam corpora download           # fetch + pin corpora
python -m redteam run --config configs/run_anthropic_baseline.yaml
python -m redteam score --run results/<run>.json
python -m redteam cross-judge --run results/<run>.judged.json
```

## Running CI locally before pushing

`scripts/ci_local.ps1` (Windows) and `scripts/ci_local.sh` (Linux/macOS) run
the **exact** same checks as `.github/workflows/ci.yml` — ruff lint, ruff
format check, mypy, pytest. Activate the venv, then:

```powershell
scripts\ci_local.ps1
```

If it exits green, CI on the PR will be green too.

## Repository layout

See `PROJECT-1-KIT.md` §6 for the target layout. `src/redteam/` holds the
schemas, corpus loaders, target adapters, defences, orchestrator, scorers, and
CLI; `configs/` holds run configs and pinned dataset versions; `results/` holds
run artifacts (gitignored — re-creatable from configs).

## Ethics

This project uses **only** published adversarial prompts. Excluded categories
(CSAM, weapons-of-mass-destruction synthesis, detailed self-harm methods) are
filtered at corpus-load time and verified by a CI test. Results are aggregate —
no raw harmful outputs are committed to this repo.

If you are a model provider whose model is included and want example
transcripts removed, email **leaffeng1115@gmail.com** — **24-hour removal
commitment**. See [`ETHICS.md`](./ETHICS.md).

## Citation

```
@software{llm_redteam_harness_2026,
  title  = {llm-redteam-harness: Reproducible LLM defence evaluation},
  author = {Ross},
  year   = {2026},
  url    = {https://github.com/rosscyking1115/llm-redteam-harness}
}
```

## Licence

MIT — see [`LICENSE`](./LICENSE).
