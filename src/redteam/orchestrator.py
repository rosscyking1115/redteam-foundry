"""Run-config loader + async orchestrator.

A run config (YAML) declares:

  - which target to use (claude-sonnet-4-6, llama3.1-8b-local, ...)
  - which defences to wrap around it, in OUTSIDE-IN order
  - which corpora subsets to draw attack cases from
  - per-run budget cap

The orchestrator validates the config (Pydantic), builds the target +
defence stack, walks the cases concurrently with bounded parallelism
(asyncio.Semaphore — Lesson L19's documented concurrency ceiling), runs
the rule-based refusal scorer on each response, and emits one JSON file
under results/<run-name>-<timestamp>.json.

Phase 3 ships ONLY the rule-based scorer. LLM-judge + Cohen's kappa
arrive in Phase 4.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from redteam.budget import reset_budget
from redteam.cache import ResponseCache
from redteam.corpora import LOADERS
from redteam.defences import DEFENCES, NEEDS_GUARD, Defence, SendLike
from redteam.schemas import AttackCase, Message
from redteam.scorers import score_refusal
from redteam.targets import TARGETS, OllamaTarget, Target


class CorpusSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source: str
    limit: int | None = None  # None = all kept cases


class DefenceSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str

    @model_validator(mode="after")
    def _id_known(self) -> DefenceSpec:
        if self.id not in DEFENCES:
            raise ValueError(f"Unknown defence id {self.id!r}. Known: {sorted(DEFENCES.keys())}")
        return self


class RunConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    target: str
    defences: list[DefenceSpec] = Field(default_factory=list)
    corpora: list[CorpusSpec]
    guard_model: str = "llama-guard4:12b"  # used only if a llamaguard4-* defence is configured
    budget_usd: Decimal = Decimal("0.50")
    concurrency: int = 4
    output_dir: Path = Path("results")
    max_tokens: int = 256

    @model_validator(mode="after")
    def _target_known(self) -> RunConfig:
        if self.target not in TARGETS:
            raise ValueError(f"Unknown target {self.target!r}. Known: {sorted(TARGETS.keys())}")
        return self

    @classmethod
    def from_yaml(cls, path: Path) -> RunConfig:
        return cls.model_validate(yaml.safe_load(path.read_text()))


# ---------------------------------------------------------------------------
# Stack assembly
# ---------------------------------------------------------------------------


def build_stack(config: RunConfig, *, cache: ResponseCache | None = None) -> SendLike:
    """Construct the (target -> defences) wrapper chain.

    `defences` in the config are listed OUTSIDE-IN: defences[0] becomes
    the outermost wrapper, the target the innermost callable.
    """
    target_cls = TARGETS[config.target]
    target: Target = target_cls(cache=cache)

    needs_guard = any(d.id in NEEDS_GUARD for d in config.defences)
    guard: SendLike | None = None
    if needs_guard:
        # Guard goes through Ollama too. Distinct OllamaTarget instance so its
        # cache key (via its own id+model) doesn't collide with the eval target.
        guard = OllamaTarget(model=config.guard_model, cache=cache)

    stack: SendLike = target
    # Apply in REVERSE so the first list entry ends up outermost.
    for spec in reversed(config.defences):
        cls = DEFENCES[spec.id]
        if spec.id in NEEDS_GUARD:
            assert guard is not None
            stack = cls(stack, guard=guard)  # type: ignore[call-arg]
        else:
            stack = cls(stack)
    return stack


# ---------------------------------------------------------------------------
# Corpus -> AttackCase iterator
# ---------------------------------------------------------------------------


def iter_attack_cases(config: RunConfig) -> list[AttackCase]:
    out: list[AttackCase] = []
    for spec in config.corpora:
        loader_cls = LOADERS.get(spec.source)
        if loader_cls is None:
            raise ValueError(
                f"Unknown corpus source {spec.source!r}. Known: {sorted(LOADERS.keys())}"
            )
        loader = loader_cls()
        loader.download()
        kept, _stats = loader.load()
        if spec.limit is not None:
            kept = kept[: spec.limit]
        out.extend(kept)
    return out


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------


class CaseOutcome(BaseModel):
    model_config = ConfigDict(extra="forbid")
    case_id: str
    case_source: str
    case_category: str
    case_severity: str
    prompt: str
    response_text: str
    finish_reason: str | None
    is_refusal: bool
    matched_phrase: str | None
    cost_usd: Decimal
    input_tokens: int
    output_tokens: int
    latency_ms: int


class RunResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    run_name: str
    target: str
    defences: list[str]
    cases_total: int
    refusals: int
    asr: float  # = (1 - refusal_rate); attack-success rate per the rule-based scorer
    refusal_rate: float
    total_cost_usd: Decimal
    started_at: str
    finished_at: str
    outcomes: list[CaseOutcome]


async def _run_case(
    stack: SendLike,
    case: AttackCase,
    sem: asyncio.Semaphore,
    *,
    max_tokens: int,
) -> CaseOutcome:
    async with sem:
        resp = await stack.send([Message(role="user", content=case.prompt)], max_tokens=max_tokens)
    score = score_refusal(resp.response_text)
    return CaseOutcome(
        case_id=case.id,
        case_source=case.source,
        case_category=case.category,
        case_severity=case.severity,
        prompt=case.prompt,
        response_text=resp.response_text,
        finish_reason=resp.finish_reason,
        is_refusal=score.is_refusal,
        matched_phrase=score.matched_phrase,
        cost_usd=resp.cost_usd,
        input_tokens=resp.input_tokens,
        output_tokens=resp.output_tokens,
        latency_ms=resp.latency_ms,
    )


async def run(config: RunConfig, *, cache_root: Path | None = None) -> RunResult:
    """Execute the run end-to-end and return a RunResult.

    Sets a fresh per-run BudgetGuard scoped to config.budget_usd so this
    call cannot drag in stray spend from other tests / runs.
    """
    reset_budget(max_per_run_usd=config.budget_usd)
    cache = ResponseCache(cache_root=cache_root) if cache_root else ResponseCache()

    stack = build_stack(config, cache=cache)
    cases = iter_attack_cases(config)
    sem = asyncio.Semaphore(config.concurrency)

    started = datetime.now(UTC).isoformat()
    outcomes = await asyncio.gather(
        *(_run_case(stack, c, sem, max_tokens=config.max_tokens) for c in cases)
    )
    finished = datetime.now(UTC).isoformat()

    refusals = sum(1 for o in outcomes if o.is_refusal)
    total = len(outcomes)
    refusal_rate = refusals / total if total else 0.0
    asr = 1.0 - refusal_rate
    total_cost = sum((o.cost_usd for o in outcomes), Decimal("0"))

    return RunResult(
        run_name=config.name,
        target=config.target,
        defences=[d.id for d in config.defences],
        cases_total=total,
        refusals=refusals,
        asr=asr,
        refusal_rate=refusal_rate,
        total_cost_usd=total_cost,
        started_at=started,
        finished_at=finished,
        outcomes=outcomes,
    )


def write_result(result: RunResult, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = result.started_at.replace(":", "-")
    path = output_dir / f"{result.run_name}-{ts}.json"
    path.write_text(result.model_dump_json(indent=2))
    return path


# Tiny convenience for tests / CLI: build a stack from an explicit list of
# defence ids without going through YAML.
def stack_from_ids(
    target: str, defence_ids: list[str], *, cache: ResponseCache | None = None
) -> SendLike:
    cfg = RunConfig(
        name="adhoc",
        target=target,
        defences=[DefenceSpec(id=d) for d in defence_ids],
        corpora=[CorpusSpec(source="advbench", limit=1)],
    )
    return build_stack(cfg, cache=cache)


# Suppress unused-warning for typing-only re-export.
_ = (Defence, Any)
