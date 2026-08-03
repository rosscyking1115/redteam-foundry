# Releasing

Checklist for cutting a release and publishing to PyPI. The build backend is
hatchling; the wheel packages `src/redteam`.

## Automated releases (recommended) — PyPI Trusted Publishing

`.github/workflows/publish.yml` builds and publishes to PyPI whenever a GitHub
**Release** is published, using **Trusted Publishing** (OIDC) — **no API token
is stored anywhere**. After the one-time setup below, releasing is just: bump
the version + CHANGELOG (§2), then create a GitHub release for the tag (§6).

### One-time setup (do once, on the PyPI website)

1. Go to <https://pypi.org/manage/project/redteam-foundry/settings/publishing/>.
2. Add a **new trusted publisher** → GitHub, with:
   - **Owner:** `rosscyking1115`
   - **Repository:** `redteam-foundry`
   - **Workflow name:** `publish.yml`
   - **Environment:** *(leave blank)*
3. Save. From then on, publishing a GitHub release runs the workflow and uploads
   to PyPI automatically.

### What the workflow refuses to publish

Three things must hold, and the first two are checked *before* the build so a
rejected release costs nothing and cannot half-happen. PyPI has no un-publish, so
every check here runs ahead of the upload rather than after it.

| Guard | Refuses |
| --- | --- |
| `publish` declares `needs: test` | a release whose lint, typecheck or test suite fails |
| `git merge-base --is-ancestor` against `main` | a tag on a commit that is not reachable from `main` |
| `test "$PKG" = "$TAG"` | a tag name that disagrees with the package version |

The third is the weakest: it establishes that two things agree about a number,
not that the code works. It is kept because it catches a mistake the other two do
not.

The `needs:` edge is the one that matters. Until 0.4.0 the workflow built and
uploaded without running anything, which made `tests/unit/test_sdist_contents.py`
a CI gate and not a release gate — the test written to stop a packaging leak did
not run on the path that publishes. `tests/unit/test_release_gate.py` now pins
the structure, because a release gate cannot be proven by releasing.

Note that the workflow **rebuilds from the tag**; it does not upload artifacts
built locally. Anything verified by hand before a release is verified against the
same source tree, not against the same bytes.

The manual, token-based steps below remain valid as a fallback (e.g. for the
very first upload, or if you prefer to publish locally). **They bypass every
guard above** — the checks live in the workflow, so a local `twine upload` has
none of them.

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
