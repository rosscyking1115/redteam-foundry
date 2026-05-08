"""JailbreakBench loader — Chao et al., 2024 (NeurIPS Datasets & Benchmarks).

Source: huggingface.co/datasets/JailbreakBench/JBB-Behaviors
File:   data/harmful-behaviors.csv  (100 harmful behaviours, 10 categories)

Columns: Index, Goal, Target, Behavior, Category, Source.

The Category field carries OpenAI-policy-style labels (e.g. "Sexual/Adult
content", "Privacy", "Disinformation"). The exclusion filter drops the
"Sexual/Adult content" category outright; everything else maps to either
`harmful_content` or `jailbreak` based on the Source field.

We download the raw CSV directly (no HF `datasets` lib required) so the
install footprint stays small and offline tests work with a fixture file.

Pinned revision: 886acc352a31533ffbcf4ef22c744658688086fc (2024-09-26).
"""

from __future__ import annotations

import csv
from collections.abc import Iterator
from pathlib import Path

import httpx

from redteam.corpora._base import CorpusLoader, stable_id
from redteam.corpora._filters import filter_prompt
from redteam.schemas import AttackCase, Category

PINNED_REVISION = "886acc352a31533ffbcf4ef22c744658688086fc"
RAW_URL = (
    f"https://huggingface.co/datasets/JailbreakBench/JBB-Behaviors/resolve/"
    f"{PINNED_REVISION}/data/harmful-behaviors.csv"
)


class JailbreakBenchLoader(CorpusLoader):
    source = "jailbreakbench"
    pinned_revision = PINNED_REVISION

    def __init__(
        self,
        cache_root: Path | None = None,
        *,
        fixture_path: Path | None = None,
    ) -> None:
        super().__init__(cache_root)
        self._fixture_path = fixture_path

    @property
    def _csv_path(self) -> Path:
        return self._fixture_path or (self.cache_dir / "harmful-behaviors.csv")

    def download(self) -> None:
        if self._fixture_path is not None:
            return
        if self._csv_path.exists():
            return
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        with httpx.Client(timeout=60.0, follow_redirects=True) as client:
            resp = client.get(RAW_URL)
            resp.raise_for_status()
            self._csv_path.write_bytes(resp.content)

    def _iter_raw(self) -> Iterator[AttackCase]:
        with self._csv_path.open(encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                goal = row.get("Goal", "").strip()
                category_label = row.get("Category", "").strip()
                if not goal:
                    continue
                cat = self._map_category(row.get("Source", ""))
                index = row.get("Index", "").strip()
                # Apply the upstream-category gate at emission time — see
                # comment in HarmBenchLoader._iter_raw for the rationale.
                gate = filter_prompt(
                    goal,
                    source="jailbreakbench",
                    source_category=category_label,
                )
                yield AttackCase(
                    id=stable_id("jailbreakbench", PINNED_REVISION, index or goal),
                    source="jailbreakbench",
                    category=cat,
                    severity="high",
                    prompt=goal,
                    expected_behaviour="refuse",
                    references=[
                        "Chao et al. 2024, JailbreakBench (NeurIPS Datasets & Benchmarks)",
                        f"https://huggingface.co/datasets/JailbreakBench/JBB-Behaviors/tree/{PINNED_REVISION}",
                        f"jbb_category={category_label}",
                    ],
                    excluded_topics=list(gate.topics) if gate.excluded else [],
                )

    @staticmethod
    def _map_category(source_field: str) -> Category:
        # JBB's `Source` distinguishes original behaviours from those derived
        # from AdvBench / Trojan Detection Challenge; we treat them all as
        # harmful_content for our taxonomy.
        _ = source_field
        return "harmful_content"


# Helper that is exercised only in the unit test, but lives here so the
# upstream-category logic is co-located with its category mapping.
def is_excluded_jbb_category(category_label: str) -> bool:
    """Return True iff the JBB Category label is in our exclusion list."""
    return filter_prompt(
        "placeholder text — category gate fires regardless",
        source="jailbreakbench",
        source_category=category_label,
    ).excluded
