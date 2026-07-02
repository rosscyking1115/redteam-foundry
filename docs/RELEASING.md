# Releasing

Checklist for cutting a release and publishing to PyPI. The build backend is
hatchling; the wheel packages `src/redteam`.

## 1. Pre-flight

- [ ] `main` is green in CI.
- [ ] Working tree clean; you are on `main` and up to date.
- [ ] `scripts/ci_local.sh` (or `.ps1`) passes: ruff, mypy --strict, pytest.

## 2. Version + changelog

- [ ] Bump the version in **both** `pyproject.toml` and
      `src/redteam/__init__.py` (they must match; `test_smoke.py` asserts it).
- [ ] Move the `CHANGELOG.md` "Unreleased" notes under a new `[X.Y.Z]` heading
      with the date, and update the compare links at the bottom.
- [ ] Follow SemVer: patch = fixes, minor = additive features, major = breaking.

## 3. Build

```bash
uv pip install build twine        # or: pipx install build twine
python -m build                   # writes dist/*.whl and dist/*.tar.gz
python -m twine check dist/*      # metadata/readme render check
```

## 4. Test-publish (recommended first time)

```bash
python -m twine upload --repository testpypi dist/*
# then, in a fresh venv:
pip install --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ redteam-foundry
redteam version && redteam --help
```

## 5. Publish

```bash
python -m twine upload dist/*     # needs a PyPI API token (~/.pypirc or env)
```

## 6. Tag + GitHub release

```bash
git tag -a vX.Y.Z -m "vX.Y.Z"
git push origin vX.Y.Z
```

- [ ] Create the GitHub release from the tag; paste the `CHANGELOG.md` section.

## 7. Smoke the published package

- [ ] Fresh venv: `pip install redteam-foundry`, then
      `redteam corpora --help` and `redteam corpora audit --help` (the offline
      path needs no API key).

## Notes

- `dist/` is build output — do not commit it (add to `.gitignore` if it appears).
- The heavy dashboard deps are an opt-in extra: `pip install "redteam-foundry[dashboard]"`.
- Live evaluation needs an `ANTHROPIC_API_KEY` (and/or local Ollama); the
  audit / staleness / dedup commands do not.
