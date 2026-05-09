#!/usr/bin/env bash
# Run the same checks GitHub Actions runs in .github/workflows/ci.yml.
# Tools invoked via `python -m TOOL` so Windows Application Control can't
# block individual binaries (false-positive on dev tools is common).
set -euo pipefail

step() {
    printf '\n=== %s ===\n' "$1"
    shift
    "$@"
}

step "ruff check (lint)"           python -m ruff check .
step "ruff format --check"         python -m ruff format --check .
step "mypy src/ (typecheck)"       python -m mypy src/
step "pytest tests/unit"           python -m pytest tests/unit -q

printf '\nAll local CI parity checks passed. Safe to push.\n'
