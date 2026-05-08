"""AdvBench loader — Zou et al., 2023.

Source: github.com/llm-attacks/llm-attacks
File:   data/advbench/harmful_behaviors.csv  (520 rows; columns: goal, target)

AdvBench has no built-in taxonomy, so every case is tagged
`category="harmful_content"`, `severity="high"`, `expected_behaviour="refuse"`.
The exclusion filter's regex layer catches the small subset of weapons-
synthesis prompts that should be dropped under ETHICS.md.

Pinned commit: 098262ed (2024-08-02). Re-pin via configs/dataset_versions.yaml.
"""

from __future__ import annotations

import csv
from collections.abc import Iterator
from pathlib import Path

import httpx

from redteam.corpora._base import CorpusLoader, stable_id
from redteam.schemas import AttackCase

PINNED_COMMIT = "098262edf85f807224e70ecd87b9d83716bf6b73"
RAW_URL = (
    f"https://raw.githubusercontent.com/llm-attacks/llm-attacks/"
    f"{PINNED_COMMIT}/data/advbench/harmful_behaviors.csv"
)


class AdvBenchLoader(CorpusLoader):
    source = "advbench"
    pinned_revision = PINNED_COMMIT

    def __init__(
        self,
        cache_root: Path | None = None,
        *,
        fixture_path: Path | None = None,
    ) -> None:
        super().__init__(cache_root)
        self._fixture_path = fixture_path  # tests pass a local CSV here

    @property
    def _csv_path(self) -> Path:
        return self._fixture_path or (self.cache_dir / "harmful_behaviors.csv")

    def download(self) -> None:
        if self._fixture_path is not None:
            return  # tests don't hit the network
        if self._csv_path.exists():
            return
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        with httpx.Client(timeout=60.0) as client:
            resp = client.get(RAW_URL)
            resp.raise_for_status()
            self._csv_path.write_bytes(resp.content)

    def _iter_raw(self) -> Iterator[AttackCase]:
        with self._csv_path.open(encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                goal = row.get("goal", "").strip()
                if not goal:
                    continue
                yield AttackCase(
                    id=stable_id("advbench", PINNED_COMMIT, goal),
                    source="advbench",
                    category="harmful_content",
                    severity="high",
                    prompt=goal,
                    expected_behaviour="refuse",
                    references=[
                        "Zou et al. 2023, Universal and Transferable Adversarial Attacks on Aligned Language Models",
                        f"https://github.com/llm-attacks/llm-attacks/tree/{PINNED_COMMIT}",
                    ],
                )
