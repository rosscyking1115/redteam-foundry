"""The release path must gate, not merely build and upload.

Until 0.4.0 `publish.yml` triggered on a published Release, built, compared the
tag name to the package version, and uploaded. It ran no tests and declared no
dependency on CI, so **`tests/unit/test_sdist_contents.py` was a CI gate and not
a release gate** — the test written to stop a packaging leak did not run on the
path that publishes. 0.4.0 was safe because its commit happened to carry a green
CI run from its pull request. That is a property of that release, not of the
mechanism.

Two guards are pinned here, both answering "what may publish?":

1. **The suite runs before the upload**, enforced by `needs:` rather than by step
   ordering or by a status check reported elsewhere. PyPI has no un-publish, so a
   check that runs after the upload can only describe what already escaped.
2. **The tagged commit is reachable from `main`.** The branch ruleset gates
   pushes to the default branch and there is no tag ruleset, so a tag on any
   commit on any branch would otherwise publish.

Also pinned: the test job must not hold `id-token: write`. GitHub scopes
permissions per job, and only the publishing job needs to mint an OIDC token.

This reads the workflow rather than running it. A release gate cannot be proven
by releasing — the behaviour is proven by breaking a test on a branch and
watching the job that `publish` depends on go red.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PUBLISH_YML = PROJECT_ROOT / ".github" / "workflows" / "publish.yml"


def _workflow() -> dict[str, Any]:
    data = yaml.safe_load(PUBLISH_YML.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _jobs() -> dict[str, Any]:
    jobs = _workflow()["jobs"]
    assert isinstance(jobs, dict)
    # Non-vacuity: an empty or renamed job map would make every check below
    # pass by having nothing to look at.
    assert len(jobs) >= 2, f"expected a test job and a publish job, found {sorted(jobs)}"
    return jobs


def test_the_workflow_still_triggers_only_on_a_published_release() -> None:
    """If the trigger changes, the guards below may no longer be on the path."""
    # PyYAML parses the bare key `on` as the boolean True.
    triggers = _workflow()[True]
    assert set(triggers) == {"release"}, f"unexpected publish triggers: {sorted(triggers)}"
    assert triggers["release"]["types"] == ["published"]


def test_publish_depends_on_the_test_job() -> None:
    """The gate. Ordering must be structural — `needs:`, not step order."""
    jobs = _jobs()
    needs = jobs["publish"].get("needs")
    needs = [needs] if isinstance(needs, str) else (needs or [])
    assert "test" in needs, (
        "the publish job does not declare `needs: test`, so the upload does not "
        "depend on the suite passing. PyPI has no un-publish."
    )
    assert "test" in jobs, "`needs: test` names a job that does not exist"


def test_the_gating_job_actually_runs_the_suite() -> None:
    """`needs:` on a job that checks nothing is a gate satisfied by absence."""
    run_steps = " ".join(
        str(step.get("run", "")) for step in _jobs()["test"]["steps"] if isinstance(step, dict)
    )
    for command in ("pytest", "ruff check", "ruff format --check", "mypy"):
        assert command in run_steps, f"the test job never runs {command!r}"


def test_the_tagged_commit_must_be_reachable_from_main() -> None:
    """Closes the second hole: tested-but-unreviewed code reaching PyPI."""
    run_steps = " ".join(
        str(step.get("run", "")) for step in _jobs()["publish"]["steps"] if isinstance(step, dict)
    )
    assert "merge-base --is-ancestor" in run_steps, (
        "the publish job does not verify the tagged commit is an ancestor of main. "
        "A tag can be created on any commit on any branch."
    )
    assert "origin/main" in run_steps, "the ancestor check names no branch to compare against"


def _step_index(steps: list[Any], needle: str) -> int:
    """Position of the first step whose name *or* action mentions `needle`.

    Both fields are searched on purpose: the upload step carries a `name:` as
    well as a `uses:`, so looking at only one of them silently finds nothing —
    and a lookup that finds nothing is not a passing check, it is no check.
    """
    for i, step in enumerate(steps):
        haystack = f"{step.get('name', '')} {step.get('uses', '')}"
        if needle in haystack:
            return i
    raise AssertionError(f"no step in the publish job mentions {needle!r}")


def test_both_verifications_precede_the_upload() -> None:
    """A check that runs after the upload describes what already escaped."""
    steps = _jobs()["publish"]["steps"]
    upload = _step_index(steps, "pypi-publish")
    for label in ("Verify the tag matches the package version", "Verify the tagged commit is on"):
        idx = _step_index(steps, label)
        assert idx < upload, f"{label!r} runs at step {idx}, after the upload at step {upload}"


def test_the_version_check_survives() -> None:
    """Weak, but not wrong, and it catches a mistake the others do not."""
    run_steps = " ".join(
        str(step.get("run", "")) for step in _jobs()["publish"]["steps"] if isinstance(step, dict)
    )
    assert 'test "$PKG" = "$TAG"' in run_steps


def test_only_the_publish_job_may_mint_a_publishing_token() -> None:
    """Least privilege, per job.

    `id-token: write` is what Trusted Publishing needs. A test job holding it is
    a wider blast radius for no benefit, and it stays invisible until someone
    looks — which is what this test is for.
    """
    workflow = _workflow()
    assert "permissions" not in workflow, (
        "workflow-level permissions apply to every job. Scope them per job so the "
        "test job cannot inherit a publishing credential."
    )
    jobs = _jobs()
    for name, job in jobs.items():
        permissions = job.get("permissions")
        assert permissions is not None, f"job {name!r} declares no permissions block"
        if name == "publish":
            assert permissions.get("id-token") == "write", "publish cannot use Trusted Publishing"
        else:
            assert "id-token" not in permissions, (
                f"job {name!r} holds id-token and does not publish"
            )
