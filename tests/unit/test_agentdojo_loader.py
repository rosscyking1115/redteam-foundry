"""AgentDojo loader tests.

Defends: the AgentDojo indirect-injection corpus loads and pins correctly, so the §8 AgentDojo cells run on the intended prompts.

If the `agentdojo` package is installed (via pip install -e .[agentdojo]),
we exercise the real loader against a small live sample. Otherwise the
loader is expected to log a warning and yield zero cases — tests assert
the graceful-degradation behavior.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from redteam.corpora.agentdojo import (
    PINNED_COMMIT,
    PINNED_VERSION,
    SUPPORTED_SUITES,
    AgentDojoLoader,
)

AGENTDOJO_AVAILABLE = importlib.util.find_spec("agentdojo") is not None


def test_loader_constants_pinned() -> None:
    assert PINNED_COMMIT == "18b501a630db736e1d0496a496d8d7aa947c596d"
    assert PINNED_VERSION == "v1.2.1"
    assert SUPPORTED_SUITES == ("workspace", "travel", "banking", "slack")


def test_loader_writes_manifest_even_without_agentdojo(tmp_path: Path) -> None:
    loader = AgentDojoLoader(cache_root=tmp_path, max_pairs_per_suite=2)
    loader.download()
    kept, stats = loader.load()
    # If agentdojo isn't installed we get 0 cases; if installed we get >0.
    if AGENTDOJO_AVAILABLE:
        assert stats.raw_count > 0
        assert all(c.source == "agentdojo" for c in kept)
        assert all(c.category == "prompt_injection_indirect" for c in kept)
    else:
        assert stats.raw_count == 0
        assert kept == []
    # Manifest is always written
    assert (tmp_path / "agentdojo" / "manifest.json").exists()


@pytest.mark.skipif(not AGENTDOJO_AVAILABLE, reason="agentdojo not installed")
def test_loader_renders_authentic_prompt_structure(tmp_path: Path) -> None:
    """When agentdojo is installed, every emitted prompt contains the
    canonical 'important instructions' injection markers."""
    loader = AgentDojoLoader(
        cache_root=tmp_path,
        suites=("workspace",),
        max_pairs_per_suite=3,
    )
    loader.download()
    kept, stats = loader.load()
    assert stats.raw_count == 3
    for case in kept:
        assert "USER REQUEST:" in case.prompt
        assert "[BEGIN TOOL OUTPUT]" in case.prompt
        assert "[END TOOL OUTPUT]" in case.prompt
        assert "<INFORMATION>" in case.prompt
        assert "</INFORMATION>" in case.prompt
        assert case.expected_behaviour == "complete_safely"
        # references include suite, user task, injection task, attack name
        ref_str = " ".join(case.references)
        assert "agentdojo_suite=workspace" in ref_str
        assert "agentdojo_attack=important_instructions" in ref_str


@pytest.mark.skipif(not AGENTDOJO_AVAILABLE, reason="agentdojo not installed")
def test_loader_respects_max_pairs(tmp_path: Path) -> None:
    """max_pairs_per_suite caps the raw count per suite (not total)."""
    loader = AgentDojoLoader(
        cache_root=tmp_path,
        suites=("workspace", "banking"),
        max_pairs_per_suite=5,
    )
    loader.download()
    kept, stats = loader.load()
    # Exactly 5 from each suite
    assert stats.raw_count == 10
    sources_per_suite: dict[str, int] = {"workspace": 0, "banking": 0}
    for case in kept:
        for ref in case.references:
            if ref.startswith("agentdojo_suite="):
                sources_per_suite[ref.split("=", 1)[1]] += 1
    assert sources_per_suite == {"workspace": 5, "banking": 5}
