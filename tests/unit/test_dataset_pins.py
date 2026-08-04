"""`configs/dataset_versions.yaml` says loaders MUST resolve to its commits.

Defends: that requirement, which until now nothing enforced (METHODOLOGY §10).

The file has always carried the rule in its own header — *"Loaders in
`src/redteam/corpora/` MUST resolve to one of these"* — and nothing read the
file. It was a written record, and a corpus pin that only a human compares is
one edit away from being wrong in a way no run would notice: a loader whose
`pinned_revision` drifts from the recorded commit still downloads, still
caches, still produces cases, and still reports a manifest. The numbers keep
coming; they are just no longer the numbers the pin claims.

This check exists because it turned out to be *cheap*, which is the useful part
of the story. It was previously argued to be impractical on the grounds that
comparing a loader to the pin needed the run manifests under `data/`, which is
gitignored and absent in CI — so any such test would skip there, and a skip is
the failure mode this repository keeps cataloguing. That reasoning was wrong.
Every loader already exposes `pinned_revision` as a **class attribute**, so the
comparison needs no network, no download cache, no fixture and no manifest:
import the registry, read the YAML, compare. It runs in CI and it bites.

The direction that matters is both ways round. A loader missing from the
config, and a config entry with no loader, are both drift — the first ships an
unpinned corpus, the second leaves a stale record that reads as coverage.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from redteam.corpora import LOADERS

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG = PROJECT_ROOT / "configs" / "dataset_versions.yaml"


def _config() -> dict[str, dict[str, object]]:
    data = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    assert isinstance(data, dict), f"{CONFIG.name} did not parse to a mapping"
    datasets = data.get("datasets")
    assert isinstance(datasets, dict), f"{CONFIG.name} has no `datasets:` mapping"
    return datasets


def _recorded_pin(entry: dict[str, object]) -> str:
    """A GitHub source records `commit`; a Hugging Face source records `revision`."""
    pin = entry.get("commit") or entry.get("revision")
    assert isinstance(pin, str) and pin, f"config entry records no commit/revision: {entry!r}"
    return pin


# ---------------------------------------------------------------------------
# Non-vacuity — the comparison must have something to compare
# ---------------------------------------------------------------------------


def test_the_config_actually_lists_datasets() -> None:
    cfg = _config()
    assert len(cfg) >= 4, f"only {len(cfg)} dataset(s) in {CONFIG.name} — the read looks broken"


def test_the_loader_registry_actually_has_loaders() -> None:
    assert len(LOADERS) >= 4, f"only {len(LOADERS)} loader(s) registered — the import looks broken"


def test_every_loader_exposes_a_pin() -> None:
    """The attribute this whole check depends on. If it vanishes, say so loudly."""
    missing = sorted(n for n, cls in LOADERS.items() if not getattr(cls, "pinned_revision", ""))
    assert missing == [], (
        f"loader(s) with no `pinned_revision`: {missing}. Without it there is nothing to "
        "compare against the config, and this suite would pass by having nothing to check."
    )


# ---------------------------------------------------------------------------
# The requirement itself
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", sorted(LOADERS))
def test_loader_resolves_to_the_pinned_commit(name: str) -> None:
    """Parametrised per loader so a failure names *which* one without reading a list."""
    cfg = _config()
    assert name in cfg, (
        f"loader {name!r} is registered but absent from {CONFIG.name}. Every corpus this "
        "harness can load must have a recorded upstream pin, or the run is unpinned."
    )
    recorded = _recorded_pin(cfg[name])
    actual = str(getattr(LOADERS[name], "pinned_revision", ""))
    assert actual == recorded, (
        f"loader {name!r} resolves to {actual!r} but {CONFIG.name} records {recorded!r}. "
        f"{CONFIG.name} states that loaders MUST resolve to one of its commits; either the "
        "loader was re-pinned without updating the config, or the config was updated "
        "without re-pinning the loader. Both mean the published provenance is wrong."
    )


def test_no_config_entry_is_left_without_a_loader() -> None:
    """The other direction: a stale record reads as coverage that does not exist."""
    orphans = sorted(set(_config()) - set(LOADERS))
    assert orphans == [], (
        f"{CONFIG.name} pins {orphans}, which no registered loader claims. A pin for a "
        "corpus nothing loads records provenance the harness cannot produce."
    )
