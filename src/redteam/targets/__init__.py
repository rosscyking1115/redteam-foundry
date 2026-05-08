"""Target adapter registry.

Each entry maps a CLI-friendly identifier to the concrete adapter class.
The CLI (`redteam targets ...`) and the orchestrator pull from here.
"""

from __future__ import annotations

from redteam.targets.anthropic import AnthropicTarget, ConfigError
from redteam.targets.base import Target
from redteam.targets.ollama import OllamaTarget, OllamaUnavailable
from redteam.targets.openai_target import OpenAITarget

TARGETS: dict[str, type[Target]] = {
    "claude-sonnet-4-6": AnthropicTarget,
    "llama3.1-8b-local": OllamaTarget,
    "gpt-5": OpenAITarget,
}

__all__ = [
    "TARGETS",
    "AnthropicTarget",
    "ConfigError",
    "OllamaTarget",
    "OllamaUnavailable",
    "OpenAITarget",
    "Target",
]
