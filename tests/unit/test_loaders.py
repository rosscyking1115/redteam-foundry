"""Loader tests — exercise each corpus loader against a tiny local fixture.

These tests deliberately do NOT hit the network. The synthetic fixtures
under tests/data/ include both benign cases (must survive the filter) and
positive cases (must be dropped), so each test doubles as a regression
test on the per-loader integration with the exclusion filter.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from redteam.corpora import (
    LOADERS,
    AdvBenchLoader,
    AgentDojoLoader,
    HarmBenchLoader,
    JailbreakBenchLoader,
)

FIXTURES = Path(__file__).parent.parent / "data"


def test_registry_has_all_four_sources() -> None:
    assert set(LOADERS.keys()) == {"advbench", "jailbreakbench", "harmbench", "agentdojo"}


# ---------------------------------------------------------------------------
# AdvBench
# ---------------------------------------------------------------------------


def test_advbench_loader_filters_synthesis_prompts(tmp_path: Path) -> None:
    loader = AdvBenchLoader(
        cache_root=tmp_path,
        fixture_path=FIXTURES / "advbench" / "harmful_behaviors_sample.csv",
    )
    loader.download()  # no-op when fixture_path is set
    kept, stats = loader.load()
    # Sample has 5 rows; 2 are WMD-synthesis prompts that the regex layer drops.
    assert stats.raw_count == 5
    assert stats.kept_count == 3
    assert stats.excluded_count == 2
    assert stats.excluded_by_topic == {"bio_chem_radiological_nuclear_weapons_synthesis": 2}
    for case in kept:
        assert case.source == "advbench"
        assert case.category == "harmful_content"
        assert case.expected_behaviour == "refuse"
        assert case.excluded_topics == []


# ---------------------------------------------------------------------------
# JailbreakBench
# ---------------------------------------------------------------------------


def test_jailbreakbench_drops_sexual_adult_content_category(tmp_path: Path) -> None:
    loader = JailbreakBenchLoader(
        cache_root=tmp_path,
        fixture_path=FIXTURES / "jailbreakbench" / "harmful-behaviors_sample.csv",
    )
    loader.download()
    kept, stats = loader.load()
    # 4 rows; 1 in the excluded "Sexual/Adult content" category.
    assert stats.raw_count == 4
    assert stats.kept_count == 3
    assert stats.excluded_count == 1
    assert stats.excluded_by_topic == {"csam": 1}
    for case in kept:
        assert case.source == "jailbreakbench"
        # The CSAM-flagged row from the fixture must NOT survive.
        assert "Sexual/Adult content" not in (r for r in case.references)


# ---------------------------------------------------------------------------
# HarmBench
# ---------------------------------------------------------------------------


def test_harmbench_drops_chemical_biological_category(tmp_path: Path) -> None:
    loader = HarmBenchLoader(
        cache_root=tmp_path,
        fixture_path=FIXTURES / "harmbench" / "harmbench_behaviors_text_all_sample.csv",
    )
    loader.download()
    _kept, stats = loader.load()
    # 4 rows; 1 in chemical_biological should be dropped via the category gate.
    # The "synthesize VX" prompt would also be dropped by the regex layer as a
    # backstop, but the category gate fires first.
    assert stats.raw_count == 4
    assert stats.kept_count == 3
    assert stats.excluded_count == 1
    assert stats.excluded_by_topic == {"bio_chem_radiological_nuclear_weapons_synthesis": 1}


# ---------------------------------------------------------------------------
# AgentDojo
# ---------------------------------------------------------------------------


def test_agentdojo_emits_canonical_patterns(tmp_path: Path) -> None:
    loader = AgentDojoLoader(cache_root=tmp_path)
    loader.download()
    kept, stats = loader.load()
    assert stats.raw_count >= 20
    assert stats.kept_count == stats.raw_count  # nothing in this set should trip the filter
    assert stats.excluded_count == 0
    categories = {c.category for c in kept}
    assert "prompt_injection_indirect" in categories
    assert "data_exfiltration" in categories


# ---------------------------------------------------------------------------
# Combined acceptance: >= 4 sources, manifest written
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("source", sorted(LOADERS.keys()))
def test_each_loader_writes_manifest(tmp_path: Path, source: str) -> None:
    loader_cls = LOADERS[source]
    fixture_map = {
        "advbench": FIXTURES / "advbench" / "harmful_behaviors_sample.csv",
        "jailbreakbench": FIXTURES / "jailbreakbench" / "harmful-behaviors_sample.csv",
        "harmbench": FIXTURES / "harmbench" / "harmbench_behaviors_text_all_sample.csv",
    }
    if source in fixture_map:
        loader = loader_cls(cache_root=tmp_path, fixture_path=fixture_map[source])  # type: ignore[call-arg]
    else:
        loader = loader_cls(cache_root=tmp_path)
    loader.download()
    loader.load()
    manifest = tmp_path / source / "manifest.json"
    assert manifest.exists(), f"no manifest written for {source}"
    body = manifest.read_text()
    assert source in body
    assert "kept_count" in body
