#!/usr/bin/env bash
# Run the same checks GitHub Actions runs in .github/workflows/ci.yml.
# Mirrors the CI job exactly. Run this before `git push` to avoid red CI.
# Activate the venv first, then: ./scripts/ci_local.sh
set -euo pipefail

step() {
    printf '\n=== %s ===\n' "$1"
    shift
    "$@"
}

step "ruff check (lint)"           ruff check .
step "ruff format --check"         ruff format --check .
step "mypy src/ (typecheck)"       mypy src/
step "pytest tests/unit"           pytest tests/unit -q

printf '\nAll local CI parity checks passed. Safe to push.\n'
