"""HarmBench loader — Mazeika et al., 2024.

Source: github.com/centerforaisafety/HarmBench
File:   data/behavior_datasets/harmbench_behaviors_text_all.csv

Columns: Behavior, FunctionalCategory, SemanticCategory, Tags, ContextString,
BehaviorID.

The SemanticCategory field carries the harm taxonomy
(`chemical_biological`, `cybercrime_intrusion`, `harmful`, `illegal`,
`misinformation_disinformation`, `harassment_bullying`, `copyright`).
The exclusion filter drops `chemical_biological` and `cbrn` outright; the
keyword-regex layer is the backstop for any prompt that slips through.

Pinned commit: 8e1604d1 (2024-08-05).
"""

from __future__ import annotations

import csv
from collections.abc import Iterator
from pathlib import Path

import httpx

from redteam.corpora._base import CorpusLoader, stable_id
from redteam.corpora._filters import filter_prompt
from redteam.schemas import AttackCase, Category

PINNED_COMMIT = "8e1604d1171fe8a48d8febecd22f600e462bdcdd"
RAW_URL = (
    f"https://raw.githubusercontent.com/centerforaisafety/HarmBench/"
    f"{PINNED_COMMIT}/data/behavior_datasets/harmbench_behaviors_text_all.csv"
)


# Map HarmBench's FunctionalCategory -> our taxonomy. Defaults to
# harmful_content when nothing matches.
_FUNCTIONAL_TO_OURS: dict[str, Category] = {
    "standard": "harmful_content",
    "contextual": "harmful_content",
    "copyright": "harmful_content",
    "multimodal": "harmful_content",
}


class HarmBenchLoader(CorpusLoader):
    source = "harmbench"
    pinned_revision = PINNED_COMMIT

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
        return self._fixture_path or (self.cache_dir / "harmbench_behaviors_text_all.csv")

    def download(self) -> None:
        if self._fixture_path is not None:
            return
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
                behavior = row.get("Behavior", "").strip()
                if not behavior:
                    continue
                semantic = (row.get("SemanticCategory") or "").strip()
                functional = (row.get("FunctionalCategory") or "").strip().lower()
                behavior_id = (row.get("BehaviorID") or "").strip()

                # Severity heuristic: WMD-adjacent semantics get "high"; the
                # rest "medium". The filter drops chemical_biological so this
                # is mostly belt-and-braces.
                severity = (
                    "high" if semantic in {"chemical_biological", "cbrn", "illegal"} else "medium"
                )

                cat: Category = _FUNCTIONAL_TO_OURS.get(functional, "harmful_content")

                # Apply the upstream-category gate here — filter_cases() in
                # _base.py only knows the prompt text, not the original
                # SemanticCategory. If the gate fires, emit with
                # excluded_topics pre-populated so filter_cases drops it
                # without rerunning the regex layer.
                gate = filter_prompt(behavior, source="harmbench", source_category=semantic)

                yield AttackCase(
                    id=stable_id("harmbench", PINNED_COMMIT, behavior_id or behavior),
                    source="harmbench",
                    category=cat,
                    severity=severity,  # type: ignore[arg-type]
                    prompt=behavior,
                    expected_behaviour="refuse",
                    references=[
                        "Mazeika et al. 2024, HarmBench",
                        f"https://github.com/centerforaisafety/HarmBench/tree/{PINNED_COMMIT}",
                        f"harmbench_semantic={semantic}",
                        f"harmbench_functional={functional}",
                    ],
                    excluded_topics=list(gate.topics) if gate.excluded else [],
                )
