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

- [ ] Bump the version in `pyproject.toml`. **That is the only place it is
      declared.** `src/redteam/__init__.py` reads the installed distribution
      metadata, so there is nothing to keep in step — this checklist used to say
      "bump it in **both**", which was the state before 0.4.1 and is exactly the
      hand-synchronised second copy whose drift shipped a wheel saying 0.4.0
      beside code saying 0.3.0. Do not re-add one.
      `tests/unit/test_version.py` (not `test_smoke.py`) asserts the version
      against `pyproject.toml`, against the installed distribution, and against
      what the CLI prints.
- [ ] After bumping, **reinstall** (`uv pip install -e ".[dev]"`) before running
      the suite locally: the installed metadata still carries the old number
      until you do, and `test_version.py` will fail on the mismatch. That is the
      test working, not a false alarm.
- [ ] Move the `CHANGELOG.md` "Unreleased" notes under a new `[X.Y.Z]` heading
      with the date, and update the compare links at the bottom.
- [ ] Follow SemVer: patch = fixes, minor = additive features, major = breaking.

> **The heading is checked for you — you are not the guard.** This step used to
> read "check the release date in that heading still matches the day you
> actually release", which put a permanent, published field behind a tickbox
> while every other release constraint was enforced in the workflow. It had
> already gone wrong: the 0.5.0 heading was first stamped with the working day
> after the calendar had rolled over.
>
> `publish.yml`'s gate job now runs `scripts/check_release_heading.py` before
> anything is built, asserting that the top-most versioned heading's **version**
> matches `pyproject.toml` and its **date** matches the release's own
> `published_at` timestamp in UTC. If the notes were prepared on one day and
> released on another, the release fails and tells you both values — it does not
> publish a wrong date and leave you to notice.
>
> The version half is additionally asserted in `tests/unit/test_release_heading.py`,
> so a bump that forgets the heading goes red on the pull request rather than at
> the release.

## 3. Build — locally, to inspect only

The workflow rebuilds from the tag and uploads what *it* built, so nothing you
build here is ever published. Build locally to look at the artifact, not to
produce the one that ships:

```bash
uv build                          # writes dist/*.whl and dist/*.tar.gz
```

`tests/unit/test_sdist_contents.py` already builds the sdist in process and
asserts it contains only git-tracked files, so the packaging check is part of
the suite rather than a manual step.

## 4. Publishing — there is no manual step, and no token

**Do not run `twine`, and do not create a PyPI API token.** Publication is
[Trusted Publishing](https://docs.pypi.org/trusted-publishers/) over OIDC:
`.github/workflows/publish.yml` mints a short-lived credential at run time, and
**no API token exists for this project anywhere.** Earlier versions of this
document ended with `python -m twine upload dist/*  # needs a PyPI API token`,
which describes a mechanism this project does not use and would send whoever
followed it looking for a secret that must not be created.

Nothing publishes until §5.

## 5. Tag, then release — and know which one is the point of no return

**Pushing the tag publishes nothing.** No workflow watches tag pushes: `ci.yml`
triggers on `pull_request` and on `push` to `main`; `publish.yml` triggers on
`release: types: [published]`. A pushed tag is therefore still reversible
(`git push --delete origin vX.Y.Z`).

```bash
git tag -a vX.Y.Z -m "vX.Y.Z"
git push origin vX.Y.Z
```

- [ ] **Publishing the GitHub release is the irreversible step.** It fires
      `publish.yml`, which runs the gate, then builds from the tag and uploads.
      **PyPI has no un-publish**: a version can be yanked, which hides it from
      resolvers, but the files and the version number are permanent and cannot
      be reused. Everything before this point can be undone; nothing after it
      can.
- [ ] Create the GitHub release from the tag; paste the `CHANGELOG.md` section.

Two guards run inside the workflow before anything is uploaded, and both refuse
rather than warn: the suite must pass (`needs: test`), and the tagged commit
must be reachable from `main`. A tag on an unreviewed branch is rejected at that
point, not published.

## 6. Smoke the published package

- [ ] Fresh venv: `pip install redteam-foundry`, then
      `redteam corpora --help` and `redteam corpora audit --help` (the offline
      path needs no API key).

## Notes

- `dist/` is build output — do not commit it (add to `.gitignore` if it appears).
- The heavy dashboard deps are an opt-in extra: `pip install "redteam-foundry[dashboard]"`.
- Live evaluation needs an `ANTHROPIC_API_KEY` (and/or local Ollama); the
  audit / staleness / dedup commands do not.
