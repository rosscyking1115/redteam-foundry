# llm-redteam-harness

> Open-source LLM red-team evaluation harness. Measures how often each
> defence stack blocks published adversarial prompts. Built as a measurement
> tool, not a weapon — see [`ETHICS.md`](./ETHICS.md).

[![CI](https://github.com/rosscyking1115/llm-redteam-harness/actions/workflows/ci.yml/badge.svg)](https://github.com/rosscyking1115/llm-redteam-harness/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/release/python-3130/)

## What this is

A reproducible benchmark that:

1. Loads ≥ 200 published adversarial prompts from AdvBench, JailbreakBench,
   HarmBench, and AgentDojo (with version-pinned commits).
2. Sends them through ≥ 2 target LLMs — Claude Sonnet 4.6 (frontier) and
   Llama 3.1 8B (local, via Ollama).
3. Toggles ≥ 4 composable defence stacks on/off — paranoid system prompt,
   Constitutional principles, Llama Guard 4 pre/post-filters, Spotlighting,
   SecAlign-style structured queries.
4. Scores responses with rule-based + LLM-judge methods, calibrated against
   a 5% human spot-check (Cohen's kappa target > 0.6).
5. Reports attack-success-rate (ASR), false-refusal rate (FRR), and cost
   per run.

See [`METHODOLOGY.md`](./METHODOLOGY.md) for the full methodology.

## Status

Pre-Phase-0 → Phase 0 (bootstrap). Build plan: nine phases over ~21 working
days, one PR per phase, CI green before merge.

## Headline matrix (TBD — populated as phases land)

| Defence stack ↓ / Attack category → | Direct jailbreak | Direct prompt injection | Indirect prompt injection | Harmful content | Data exfiltration |
| --- | --- | --- | --- | --- | --- |
| Baseline (no defence) | TBD | TBD | TBD | TBD | TBD |
| + Paranoid system prompt | | | | | |
| + Constitutional principles | | | | | |
| + Llama Guard 4 pre-filter | | | | | |
| + Llama Guard 4 post-filter | | | | | |
| + Spotlighting | n/a | n/a | TBD | n/a | n/a |
| + SecAlign-style structured queries | n/a | TBD | TBD | n/a | TBD |
| Full stack | | | | | |

Plus FRR on a 50-prompt benign control set.

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
redteam version                     # prints 0.1.0
```

Hard $5/run budget cap is enforced inside `Target.send` (see Lesson L3 in
`PROJECT-1-KIT.md`). Set a matching console cap before first run.

## Running CI locally before pushing

`scripts/ci_local.ps1` (Windows) and `scripts/ci_local.sh` (Linux/macOS) run
the **exact** same checks that `.github/workflows/ci.yml` runs — ruff lint,
ruff format --check, mypy, pytest. Activate the venv, then:

```powershell
scripts\ci_local.ps1
```

If it exits green, CI on the PR will be green too. If it fails, fix locally
before `git push`.

## Repository layout

See `PROJECT-1-KIT.md` §6 for the target layout. Phase-0 skeleton populates
the directory tree but most modules are empty stubs until their phase lands.

## Ethics

This project uses **only** published adversarial prompts. Excluded
categories (CSAM, weapons-of-mass-destruction synthesis, detailed self-harm
methods) are filtered at corpus-load time and verified by a CI test.
Aggregate results only — no raw harmful outputs in this repo.

If you are a model provider whose model is included and want example
transcripts removed, email **leaffeng1115@gmail.com** —
**24-hour removal commitment**. See [`ETHICS.md`](./ETHICS.md).

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
