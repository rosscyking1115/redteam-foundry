# Contributing

Thanks for your interest. This is a research tool for **auditing adversarial
benchmarks**; contributions that sharpen that focus are very welcome.

## Scope

In scope: corpus quality/dedup, benchmark staleness, defence measurement,
multilingual over-refusal, safe challenge-pack export, and corpus/target/judge
adapters.

Out of scope (by design): production release-gating — ship/warn/block, incident
replay, policy-as-code. That belongs in a downstream layer; see
[`docs/ROADMAP.md`](docs/ROADMAP.md) and the README's positioning.

## Ethics (please read before adding corpora or prompts)

- Use **only published** adversarial prompts, commit-pinned. Do not author novel
  jailbreaks, in any language (see [`ETHICS.md`](ETHICS.md)).
- Excluded categories (CSAM, WMD synthesis, detailed self-harm methods) are
  filtered at load time and enforced by `tests/unit/test_exclusion_filter.py`.
  If you add a corpus, add positive/benign cases there proving nothing leaks.
- Don't commit raw harmful prompts or model outputs. Reports and packs quote
  truncated previews or redact adversarial prompts.

## Dev setup

```bash
uv venv --python 3.13
source .venv/bin/activate        # .venv\Scripts\activate on Windows
uv pip install -e ".[dev]"
pre-commit install
```

## Before you open a PR

Run the exact CI checks locally — green here means green on the PR:

```bash
scripts/ci_local.sh              # or scripts\ci_local.ps1 on Windows
# = ruff check + ruff format --check + mypy (strict) + pytest tests/unit
```

Guidelines:
- One focused change per PR; keep the test suite green (`pytest tests/unit`).
- New behaviour needs a unit test. Analysis functions should be pure and
  testable without network/API access.
- Type-annotate everything (`mypy --strict` must pass). No new heavy runtime
  dependencies without discussion.
- CI runs no live API calls; don't add tests that require one to unit-test.

## Reporting issues

Bugs, stale/duplicated benchmark findings, and requests to audit a specific
corpus are all useful. Include the command you ran and the (aggregate) output.
For anything sensitive — a suspected leak past the exclusion filter, or a
model-provider takedown — email **rosscyking@gmail.com** (see `ETHICS.md`).
