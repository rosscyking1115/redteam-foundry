"""Module entrypoint so `python -m redteam ...` works the same as `redteam ...`.

This is the second-line workaround for environments where the `redteam.exe`
console script is blocked by Windows Application Control / Smart App Control
(a known false-positive on dev tools). With this shim:

    python -m redteam corpora list

is equivalent to:

    redteam corpora list
"""

from __future__ import annotations

from redteam.cli import app

if __name__ == "__main__":
    app()
