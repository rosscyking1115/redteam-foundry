"""Control-harness tests.

Defends: that a control harness can never be mistaken for a defence, in the
registry, in a run artifact, or in corpus-level analysis. A control forces a
known outcome to test the measurement; reading one as a model result would
manufacture exactly the unattributable metric this project exists to criticise
(METHODOLOGY section 12.7).
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from redteam.controls import (
    CONTROL_PREFIX,
    CONTROLS,
    InjectionCompliantControl,
    control_marker,
    is_control_run,
)
from redteam.defences import DEFENCES
from redteam.orchestrator import RunConfig, build_stack
from redteam.schemas import Message, TargetResponse

# ---------------------------------------------------------------------------
# The registries must stay separate — and that must be enforced, not conventional
# ---------------------------------------------------------------------------


def test_no_control_is_registered_as_a_defence() -> None:
    """A control in DEFENCES could be selected by a `defences:` config key."""
    assert set(CONTROLS) & set(DEFENCES) == set(), "control id leaked into the defence registry"


def test_every_control_marks_itself_with_the_prefix() -> None:
    for control_id, cls in CONTROLS.items():
        assert cls.defence_id == f"{CONTROL_PREFIX}{control_id}", (
            f"{cls.__name__}.defence_id must derive from control_id so they cannot drift"
        )


def test_control_marker_matches_the_class_attribute() -> None:
    """The artifact string and the wrapper's own id must not diverge."""
    for control_id, cls in CONTROLS.items():
        assert control_marker(control_id) == cls.defence_id


# ---------------------------------------------------------------------------
# is_control_run — the guard that keeps controls out of corpus analysis
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("defences", "expected"),
    [
        ([], False),
        (["system-prompt"], False),
        (["system-prompt", "spotlighting"], False),
        (["control:injection-compliant"], True),
        (["system-prompt", "control:injection-compliant"], True),
    ],
)
def test_is_control_run(defences: list[str], expected: bool) -> None:
    assert is_control_run(defences) is expected


def test_a_control_run_is_neither_baseline_nor_defended() -> None:
    """Both naive partitions get a control wrong, which is why it is excluded.

    `not defences` would call it a baseline; a truthy `defences` would call it
    defended. A detector control has a deliberately high ASR against a low
    baseline, so counting it as defended inverts `low_defence_sensitivity`.
    """
    marker = [control_marker("injection-compliant")]
    assert marker != []  # would be read as "baseline"
    assert bool(marker)  # would be read as "defended"
    assert is_control_run(marker)  # so callers must ask this instead


# ---------------------------------------------------------------------------
# Wiring — a control must be visible in the config and in the artifact
# ---------------------------------------------------------------------------


def _cfg(**kw: object) -> RunConfig:
    base: dict[str, object] = {
        "name": "t",
        "target": "llama3.1-8b-local",
        "corpora": [{"source": "advbench", "limit": 1}],
    }
    base.update(kw)
    return RunConfig.model_validate(base)


def test_unknown_control_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unknown control"):
        _cfg(controls=["not-a-control"])


def test_known_control_validates_and_wraps_outermost() -> None:
    cfg = _cfg(controls=["injection-compliant"])
    assert cfg.controls == ["injection-compliant"]
    stack = build_stack(cfg)
    assert isinstance(stack, InjectionCompliantControl)


def test_control_run_is_not_recorded_as_undefended() -> None:
    """The artifact must never read `defences: []` when a control was applied."""
    cfg = _cfg(controls=["injection-compliant"])
    recorded = [d.id for d in cfg.defences] + [control_marker(c) for c in cfg.controls]
    assert recorded != []
    assert recorded == ["control:injection-compliant"]
    assert is_control_run(recorded)


def test_the_shipped_detector_control_config_declares_a_control() -> None:
    """Guards the real config: a control silently dropping to `defences: []`
    would turn an engineered result into what looks like a model result."""
    repo_root = Path(__file__).resolve().parents[2]
    cfg = RunConfig.from_yaml(repo_root / "configs" / "run_agentdojo_detector_control.yaml")
    assert cfg.controls == ["injection-compliant"]
    assert cfg.defences == []
    assert cfg.target == "llama3.1-8b-local", "must match the section 8 AgentDojo Llama rows"


# ---------------------------------------------------------------------------
# Behaviour — the compliance instruction actually reaches the target
# ---------------------------------------------------------------------------


class _Recorder:
    """Minimal SendLike that captures the system prompt it was handed."""

    # Defence.__init__ composes its own id/model_version from the inner one's.
    id = "recorder"
    model_version = "test"

    def __init__(self) -> None:
        self.system: str | None = None

    async def send(
        self,
        messages: list[Message],
        *,
        system: str | None = None,
        max_tokens: int = 1024,
    ) -> TargetResponse:
        self.system = system
        return TargetResponse(
            target_id=self.id,
            request_messages=list(messages),
            response_text="ok",
            finish_reason="stop",
            cost_usd=Decimal("0"),
            input_tokens=1,
            output_tokens=1,
            latency_ms=1,
            model_version=self.model_version,
            attempt=1,
        )


async def test_control_instructs_the_model_to_trust_tool_output() -> None:
    inner = _Recorder()
    await InjectionCompliantControl(inner).send([Message(role="user", content="hi")])
    assert inner.system is not None
    system = inner.system.lower()
    assert "tool output" in system
    assert "authoritative" in system


async def test_control_preserves_a_caller_supplied_system_prompt() -> None:
    inner = _Recorder()
    await InjectionCompliantControl(inner).send(
        [Message(role="user", content="hi")], system="CALLER"
    )
    assert inner.system is not None
    assert "CALLER" in inner.system
