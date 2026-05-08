"""Corpus loader registry.

Each entry maps the canonical Source string used in AttackCase.source to
the concrete CorpusLoader subclass. The CLI (`redteam corpora ...`) uses
this registry to enumerate available datasets.
"""

from __future__ import annotations

from redteam.corpora._base import CorpusLoader, LoadStats, stable_id
from redteam.corpora._filters import filter_cases, filter_prompt
from redteam.corpora.advbench import AdvBenchLoader
from redteam.corpora.agentdojo import AgentDojoLoader
from redteam.corpora.harmbench import HarmBenchLoader
from redteam.corpora.jailbreakbench import JailbreakBenchLoader

LOADERS: dict[str, type[CorpusLoader]] = {
    "advbench": AdvBenchLoader,
    "jailbreakbench": JailbreakBenchLoader,
    "harmbench": HarmBenchLoader,
    "agentdojo": AgentDojoLoader,
}

__all__ = [
    "LOADERS",
    "AdvBenchLoader",
    "AgentDojoLoader",
    "CorpusLoader",
    "HarmBenchLoader",
    "JailbreakBenchLoader",
    "LoadStats",
    "filter_cases",
    "filter_prompt",
    "stable_id",
]
