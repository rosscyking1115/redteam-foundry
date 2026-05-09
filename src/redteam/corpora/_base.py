"""Base class for dataset loaders.

Each concrete loader downloads a published adversarial dataset, normalises
it into AttackCase objects, applies the exclusion filter at load time, and
writes a manifest of what was kept vs dropped.

Loaders are deliberately thin: download -> iterate raw -> emit AttackCase.
The filter is applied in `load()` so individual loaders can't accidentally
skip it.
"""

from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

from redteam.corpora._filters import filter_cases
from redteam.schemas import AttackCase, Source

DEFAULT_CACHE_ROOT = Path("data/cache")


@dataclass
class LoadStats:
    """Summary of one load() call. Persisted to manifest.json."""

    source: Source
    raw_count: int
    kept_count: int
    excluded_count: int
    excluded_by_topic: dict[str, int] = field(default_factory=dict)
    pinned_revision: str = ""


class CorpusLoader(ABC):
    """Subclass to wrap a single upstream adversarial dataset."""

    # Class attributes — set on each concrete subclass.
    source: Source
    pinned_revision: str  # commit hash or HF dataset revision

    def __init__(self, cache_root: Path | None = None) -> None:
        self.cache_root = cache_root or DEFAULT_CACHE_ROOT
        self.cache_dir = self.cache_root / self.source

    # ---- Subclasses implement -------------------------------------------

    @abstractmethod
    def download(self) -> None:
        """Materialise raw data into self.cache_dir. Idempotent."""

    @abstractmethod
    def _iter_raw(self) -> Iterator[AttackCase]:
        """Yield AttackCase objects from cached raw data, BEFORE filtering."""

    # ---- Shared, do not override ----------------------------------------

    def load(self) -> tuple[list[AttackCase], LoadStats]:
        """Iterate raw cases, apply exclusion filter, write manifest."""
        raw = list(self._iter_raw())
        kept, excluded = filter_cases(raw)
        stats = LoadStats(
            source=self.source,
            raw_count=len(raw),
            kept_count=len(kept),
            excluded_count=len(excluded),
            excluded_by_topic=self._tally_excluded(excluded),
            pinned_revision=self.pinned_revision,
        )
        self._write_manifest(stats)
        return kept, stats

    @staticmethod
    def _tally_excluded(excluded: list[AttackCase]) -> dict[str, int]:
        out: dict[str, int] = {}
        for case in excluded:
            for topic in case.excluded_topics:
                out[topic] = out.get(topic, 0) + 1
        return out

    def _write_manifest(self, stats: LoadStats) -> None:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        (self.cache_dir / "manifest.json").write_text(
            json.dumps(
                {
                    "source": stats.source,
                    "raw_count": stats.raw_count,
                    "kept_count": stats.kept_count,
                    "excluded_count": stats.excluded_count,
                    "excluded_by_topic": stats.excluded_by_topic,
                    "pinned_revision": stats.pinned_revision,
                },
                indent=2,
            ),
            encoding="utf-8",
        )


def stable_id(*parts: str) -> str:
    """Stable 12-char SHA1 prefix from joined parts. Use for AttackCase.id."""
    return hashlib.sha1("\n".join(parts).encode("utf-8")).hexdigest()[:12]
