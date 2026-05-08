"""Defence registry.

Map defence ids (used in YAML configs) to the wrapper classes. The
orchestrator (Phase 3 / Phase 4) walks a config's `defences:` list and
nests them around the chosen target.

Order in the config matters: defences listed earlier sit OUTSIDE later
ones, so post-filters land outside pre-filters etc. The build_stack()
helper applies them in list order: stack[0] becomes the outermost.
"""

from __future__ import annotations

from redteam.defences.base import Defence, SendLike, merge_system, synthetic_refusal
from redteam.defences.constitutional import ConstitutionalDefence
from redteam.defences.llama_guard import LlamaGuard4PostFilter, LlamaGuard4PreFilter
from redteam.defences.secalign import SecAlignStructuredQueryDefence
from redteam.defences.spotlighting import SpotlightingDefence
from redteam.defences.system_prompt import SystemPromptDefence

DEFENCES: dict[str, type[Defence]] = {
    "system-prompt": SystemPromptDefence,
    "constitutional": ConstitutionalDefence,
    "spotlighting": SpotlightingDefence,
    "secalign": SecAlignStructuredQueryDefence,
    "llamaguard4-pre": LlamaGuard4PreFilter,
    "llamaguard4-post": LlamaGuard4PostFilter,
}

# Defences that need an extra `guard` SendLike injected at construction time.
NEEDS_GUARD: set[str] = {"llamaguard4-pre", "llamaguard4-post"}


__all__ = [
    "DEFENCES",
    "NEEDS_GUARD",
    "ConstitutionalDefence",
    "Defence",
    "LlamaGuard4PostFilter",
    "LlamaGuard4PreFilter",
    "SecAlignStructuredQueryDefence",
    "SendLike",
    "SpotlightingDefence",
    "SystemPromptDefence",
    "merge_system",
    "synthetic_refusal",
]
