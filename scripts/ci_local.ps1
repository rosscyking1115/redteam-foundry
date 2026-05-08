<#
.SYNOPSIS
    Run the same checks GitHub Actions runs in .github/workflows/ci.yml.

.DESCRIPTION
    Mirrors the CI job exactly — ruff lint, ruff format --check, mypy, pytest.
    Run this before `git push` to avoid red CI on PRs. Exit code is non-zero
    if any check fails.

.NOTES
    Activate the venv first:
        .venv\Scripts\Activate.ps1
    Then:
        scripts\ci_local.ps1
#>

$ErrorActionPreference = "Stop"

function Step($name, [scriptblock]$body) {
    Write-Host ""
    Write-Host "=== $name ===" -ForegroundColor Cyan
    & $body
    if ($LASTEXITCODE -ne 0) {
        Write-Host "FAIL: $name (exit $LASTEXITCODE)" -ForegroundColor Red
        exit $LASTEXITCODE
    }
}

Step "ruff check (lint)"            { ruff check . }
Step "ruff format --check"          { ruff format --check . }
Step "mypy src/ (typecheck)"        { mypy src/ }
Step "pytest tests/unit"            { pytest tests/unit -q }

Write-Host ""
Write-Host "All local CI parity checks passed. Safe to push." -ForegroundColor Green
