"""LLM red-team evaluation harness.

See METHODOLOGY.md for the methodology.
"""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _installed_version

try:
    # Read the version from the installed distribution rather than restating it.
    #
    # This was a hardcoded string, kept in step with `pyproject.toml` by hand,
    # and 0.4.0 is where that finally failed: `pyproject.toml` was bumped and
    # this file was not, so the published 0.4.0 wheel carries METADATA saying
    # 0.4.0 and code saying 0.3.0, and `redteam version` tells users 0.3.0.
    #
    # Two sources of truth for one fact will drift; the only question is when.
    # `tests/unit/test_version.py` now pins them equal so the drift cannot
    # silently recur, and this lookup means there is nothing to keep in step.
    __version__ = _installed_version("redteam-foundry")
except PackageNotFoundError:  # pragma: no cover - only when running from a source tree
    # Not installed (e.g. a bare source checkout on sys.path). Say so rather
    # than guessing a number that would then be wrong in a new way.
    __version__ = "0.0.0+unknown"

__all__ = ["__version__"]
