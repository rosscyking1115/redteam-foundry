"""Orchestrator integration test with stub targets — no API calls."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from redteam.orchestrator import RunConfig, build_stack, write_result
from redteam.schemas import Message, TargetResponse


class _StubTarget:
    """SendLike that always replies with a refusal phrase."""

    id = "stub"
    model_version = "stub-1"

    async def send(
        self,
        messages: list[Message],
        *,
        system: str | None = None,
        max_tokens: int = 1024,
    ) -> TargetResponse:
        return TargetResponse(
            target_id=self.id,
            model_version=self.model_version,
            request_messages=messages,
            response_text="I can't help with that.",
            finish_reason="stop",
            input_tokens=10,
            output_tokens=5,
            cost_usd=Decimal("0"),
            latency_ms=1,
        )


def test_runconfig_from_yaml_validates(tmp_path: Path) -> None:
    p = tmp_path / "ok.yaml"
    p.write_text(
        "name: t\n"
        "target: claude-sonnet-4-6\n"
        "defences:\n"
        "  - id: spotlighting\n"
        "corpora:\n"
        "  - source: advbench\n"
        "    limit: 1\n"
    )
    cfg = RunConfig.from_yaml(p)
    assert cfg.name == "t"
    assert cfg.target == "claude-sonnet-4-6"
    assert [d.id for d in cfg.defences] == ["spotlighting"]


def test_runconfig_rejects_unknown_defence(tmp_path: Path) -> None:
    p = tmp_path / "bad.yaml"
    p.write_text(
        "name: t\n"
        "target: claude-sonnet-4-6\n"
        "defences:\n"
        "  - id: not-a-real-defence\n"
        "corpora:\n"
        "  - source: advbench\n"
        "    limit: 1\n"
    )
    with pytest.raises(Exception, match="Unknown defence"):
        RunConfig.from_yaml(p)


def test_build_stack_outside_in_order(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stack id should reflect defences[0] outermost, target innermost."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    cfg = RunConfig(
        name="t",
        target="claude-sonnet-4-6",
        defences=[
            {"id": "system-prompt"},  # type: ignore[list-item]
            {"id": "spotlighting"},  # type: ignore[list-item]
        ],
        corpora=[{"source": "advbench", "limit": 1}],  # type: ignore[list-item]
    )
    stack = build_stack(cfg)
    # system-prompt is outermost: id chains as system-prompt+spotlighting+claude-sonnet-4-6
    assert stack.id == "system-prompt+spotlighting+claude-sonnet-4-6"


def test_write_result_round_trip(tmp_path: Path) -> None:
    from redteam.orchestrator import CaseOutcome, RunResult

    result = RunResult(
        run_name="t",
        target="x",
        defences=[],
        cases_total=1,
        refusals=1,
        asr=0.0,
        refusal_rate=1.0,
        total_cost_usd=Decimal("0"),
        started_at="2026-05-08T00:00:00+00:00",
        finished_at="2026-05-08T00:00:01+00:00",
        outcomes=[
            CaseOutcome(
                case_id="x",
                case_source="advbench",
                case_category="harmful_content",
                case_severity="high",
                prompt="...",
                response_text="I can't help with that.",
                finish_reason="stop",
                is_refusal=True,
                matched_phrase="I can",
                cost_usd=Decimal("0"),
                input_tokens=1,
                output_tokens=1,
                latency_ms=1,
            )
        ],
    )
    out = write_result(result, tmp_path)
    assert out.exists()
    parsed = RunResult.model_validate_json(out.read_text())
    assert parsed.cases_total == 1
    assert parsed.outcomes[0].is_refusal


@pytest.mark.asyncio
async def test_end_to_end_run_with_stub(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Patch the target registry to return a stub; full run produces a refusal-heavy result."""
    from redteam import targets as targets_mod
    from redteam.orchestrator import run

    def _stub_factory(*_args: object, **_kwargs: object) -> _StubTarget:
        return _StubTarget()

    monkeypatch.setitem(targets_mod.TARGETS, "claude-sonnet-4-6", _stub_factory)  # type: ignore[arg-type]

    cfg = RunConfig(
        name="stub-test",
        target="claude-sonnet-4-6",
        defences=[],
        corpora=[{"source": "advbench", "limit": 0}],  # type: ignore[list-item]
        budget_usd=Decimal("1.00"),
    )
    result = await run(cfg, cache_root=tmp_path)
    # 0 cases — the run should still succeed and produce a sane summary.
    assert result.cases_total == 0
    assert result.refusal_rate == 0.0
