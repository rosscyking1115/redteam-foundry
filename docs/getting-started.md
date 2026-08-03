# Getting started

Install, set up for development, and reproduce the published result. The offline
audit, staleness and dedup paths need no API key.

## Install the CLI

```bash
pipx install redteam-foundry     # recommended — puts `redteam` on your PATH
# or: pip install redteam-foundry
redteam --help
```

## Clone for development

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

Dependencies are pinned in [`uv.lock`](../uv.lock) for a byte-for-byte
reproducible environment.

> [!WARNING]
> Live runs call paid APIs. Each run enforces a hard USD budget cap (set per
> config in `configs/`), and the judge and target adapters enforce a per-call
> cap — but set a matching **console budget cap** before your first run anyway.

## Reproduce the headline table

The 12-cell table is regenerated straight from the cached cross-judged run
artifacts — no API calls — and can be asserted against the frozen published
numbers in one command:

```bash
python scripts/headline_table.py          # print the AdvBench + AgentDojo tables
python scripts/headline_table.py --check  # also assert they match METHODOLOGY.md §8
```

The run artifacts are gitignored, because they contain prompt and response text
(see [`ETHICS.md`](../ETHICS.md)), but they are free and deterministic to
regenerate from the response cache with `redteam run` / `score` / `cross-judge`.

## Development

`scripts/ci_local.ps1` (Windows) and `scripts/ci_local.sh` (Linux and macOS) run
the same checks as CI — ruff lint, ruff format check, mypy, pytest. Green locally
means green on the PR. See [`tests/README.md`](../tests/README.md) for which
claim each test suite defends.

Run artifacts (`results/`), audit outputs (`reports/`) and non-sample packs
(`challenge_packs/`) are gitignored — all re-creatable from configs.

**Typing.** `mypy` runs in `strict` mode with `warn_unreachable`
([`pyproject.toml`](../pyproject.toml)), and CI fails the build on any type
error — it is a gate, not a report. Coverage is all of `src/`; `tests/` and
`scripts/` are linted and formatted but not yet typechecked.

**Result integrity.** `python scripts/headline_table.py --check` recomputes every
published cell from the cached run artifacts and fails on drift — including
whether each cross-judge κ is a real measurement or a degenerate `0/0` (see
[`METHODOLOGY.md`](../METHODOLOGY.md) §7). The artifacts are gitignored, so this
runs locally rather than in CI; `tests/unit/test_headline_table.py` pins the
classification logic itself, which does run in CI.

**Releasing.** See [`RELEASING.md`](RELEASING.md). The release path runs the full
suite before it can publish and refuses a tag that is not reachable from `main`.

## Related

- [Command reference](commands.md) — every sub-command, offline and live
- [`CONTRIBUTING.md`](../CONTRIBUTING.md) — scope, and the ethics rules for
  adding corpora
