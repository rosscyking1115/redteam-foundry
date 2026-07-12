"""Challenge-pack exporter (Phase 5).

Packages validated scenarios into a versioned, self-describing **challenge
pack** that a downstream release-gate system can consume as a regression suite:

    <pack_id>/
      pack.yaml         # metadata: id, version, languages, families, caveats
      scenarios.jsonl   # one scenario per line
      datacard.md       # human-readable pack card

Safety model
------------
Benign scenarios (the control sets) ship with their full prompt — they are
harmless by construction. Adversarial scenarios are **redacted by default**:
the pack carries the id, taxonomy, a SHA-256 of the prompt, and a short
preview, but not the raw harmful text. Downstream consumers re-materialise the
full prompt from the pinned upstream corpus via the harness, so this repo never
re-hosts harmful content. `include_adversarial_prompts=True` overrides this for
a trusted, private context.

This module only *exports*; it makes no release decision. Passing a pack is not
proof of safety — that caveat travels inside every pack (`safety_notes`).
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field

from redteam.corpora.taxonomy import detect_language, infer_attack_families
from redteam.schemas import AttackCase

# Sources whose prompts are adversarial and must be redacted by default.
_ADVERSARIAL_SOURCES = frozenset({"advbench", "jailbreakbench", "harmbench", "agentdojo"})

_WS = re.compile(r"\s+")

# A pack_id doubles as the output directory name (CLI writes <output>/<pack_id>),
# so it must be a single safe path segment. This pattern forbids path separators,
# leading dots, and absolute paths — closing the traversal / absolute-path-
# substitution that `pathlib`'s `output_dir / pack_id` would otherwise allow.
_PACK_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")

_DEFAULT_RECOMMENDED = ("benchmark_research", "release_gate_regression")
_DEFAULT_NOT_RECOMMENDED = ("standalone_deployment_approval",)


def validate_pack_id(pack_id: str) -> str:
    """Return `pack_id` unchanged if it is a safe path segment, else raise.

    Guards the `<output>/<pack_id>` write path against directory traversal
    (`../…`) and absolute-path substitution (`/etc/…`, which `pathlib` treats as
    replacing the base entirely). Enforced at the library boundary so every
    caller — CLI or programmatic — gets the same guarantee.
    """
    if not _PACK_ID_RE.match(pack_id):
        raise ValueError(
            f"invalid pack_id {pack_id!r}: must match {_PACK_ID_RE.pattern} — "
            "letters/digits/'.'/'_'/'-', starting alphanumeric, no path separators."
        )
    return pack_id


def _preview(text: str, *, limit: int = 60) -> str:
    flat = _WS.sub(" ", text.strip())
    return flat if len(flat) <= limit else flat[:limit].rstrip() + "…"


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class Scenario(BaseModel):
    """One packaged scenario. `prompt` is None when redacted."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    source: str
    category: str
    severity: str
    lang: str | None
    attack_families: list[str]
    expected_behaviour: str
    prompt: str | None
    prompt_sha256: str
    prompt_preview: str


class ChallengePack(BaseModel):
    """Pack metadata — everything except the scenarios themselves."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    pack_id: str
    version: str
    description: str
    created_at: str
    n_scenarios: int
    sources: list[str]
    languages: list[str]
    attack_families: list[str]
    harm_categories: list[str]
    scenarios_redacted: bool
    recommended_use: list[str]
    not_recommended_for: list[str]
    expected_controls: list[str] = Field(default_factory=list)
    safety_notes: list[str]


def build_challenge_pack(
    cases: Sequence[AttackCase],
    *,
    pack_id: str,
    version: str = "1.0.0",
    description: str = "",
    recommended_use: Sequence[str] = _DEFAULT_RECOMMENDED,
    not_recommended_for: Sequence[str] = _DEFAULT_NOT_RECOMMENDED,
    expected_controls: Sequence[str] = (),
    include_adversarial_prompts: bool = False,
) -> tuple[ChallengePack, list[Scenario]]:
    """Build a pack (metadata + scenarios) from a set of AttackCases. Pure."""
    validate_pack_id(pack_id)
    scenarios: list[Scenario] = []
    any_redacted = False
    for case in cases:
        redact = case.source in _ADVERSARIAL_SOURCES and not include_adversarial_prompts
        any_redacted = any_redacted or redact
        lang = case.lang or detect_language(case.prompt).label
        scenarios.append(
            Scenario(
                id=case.id,
                source=case.source,
                category=case.category,
                severity=case.severity,
                lang=lang,
                attack_families=list(infer_attack_families(case.prompt)),
                expected_behaviour=case.expected_behaviour,
                prompt=None if redact else case.prompt,
                prompt_sha256=_sha256(case.prompt),
                prompt_preview=_preview(case.prompt),
            )
        )

    sources = sorted({s.source for s in scenarios})
    languages = sorted({s.lang for s in scenarios if s.lang})
    families = sorted({f for s in scenarios for f in s.attack_families})
    harm_categories = sorted({s.category for s in scenarios})

    safety_notes = [
        "Passing this pack is NOT proof of safety; it is a regression check on "
        "specific, static scenarios.",
        "Not a substitute for incident replay, policy-as-code gates, or a "
        "release decision — those belong in a downstream release-gate layer.",
    ]
    if any_redacted:
        safety_notes.insert(
            0,
            "Adversarial prompts are redacted (SHA-256 + preview only); "
            "re-materialise them from the pinned upstream corpus via the harness.",
        )

    pack = ChallengePack(
        pack_id=pack_id,
        version=version,
        description=description,
        created_at=datetime.now(UTC).isoformat(),
        n_scenarios=len(scenarios),
        sources=sources,
        languages=languages,
        attack_families=families,
        harm_categories=harm_categories,
        scenarios_redacted=any_redacted,
        recommended_use=list(recommended_use),
        not_recommended_for=list(not_recommended_for),
        expected_controls=list(expected_controls),
        safety_notes=safety_notes,
    )
    return pack, scenarios


def render_pack_datacard(pack: ChallengePack) -> str:
    p = pack
    lines = [
        f"# Challenge pack card — {p.pack_id}",
        "",
        f"- **Version:** {p.version}",
        f"- **Scenarios:** {p.n_scenarios}",
        f"- **Created:** {p.created_at}",
        f"- **Sources:** {', '.join(p.sources)}",
        f"- **Languages:** {', '.join(p.languages) or '—'}",
        f"- **Attack families:** {', '.join(p.attack_families) or '—'}",
        f"- **Harm categories:** {', '.join(p.harm_categories)}",
        f"- **Prompts redacted:** {'yes' if p.scenarios_redacted else 'no'}",
        "",
        f"{p.description}" if p.description else "",
        "",
        "## Recommended use",
        "",
        *[f"- {u}" for u in p.recommended_use],
        "",
        "## Not recommended for",
        "",
        *[f"- {u}" for u in p.not_recommended_for],
        "",
    ]
    if p.expected_controls:
        lines += ["## Expected controls", "", *[f"- {c}" for c in p.expected_controls], ""]
    lines += ["## Safety notes", "", *[f"- {n}" for n in p.safety_notes], ""]
    return "\n".join(lines)


def write_challenge_pack(pack: ChallengePack, scenarios: Sequence[Scenario], out_dir: Path) -> Path:
    """Write pack.yaml + scenarios.jsonl + datacard.md into `out_dir`."""
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "pack.yaml").write_text(
        yaml.safe_dump(pack.model_dump(), sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    with (out_dir / "scenarios.jsonl").open("w", encoding="utf-8") as fh:
        for s in scenarios:
            fh.write(s.model_dump_json() + "\n")
    (out_dir / "datacard.md").write_text(render_pack_datacard(pack), encoding="utf-8")
    return out_dir


def read_challenge_pack(pack_dir: Path) -> tuple[ChallengePack, list[Scenario]]:
    """Read a pack written by `write_challenge_pack` — the inverse operation.

    This is the entry point a downstream consumer (e.g. a release-gate layer)
    calls to load a pack as a regression suite. See
    `examples/export_to_agent_release_gates.md` for the consumption contract.
    """
    pack = ChallengePack.model_validate(
        yaml.safe_load((pack_dir / "pack.yaml").read_text(encoding="utf-8"))
    )
    scenarios: list[Scenario] = []
    for line in (pack_dir / "scenarios.jsonl").read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped:
            scenarios.append(Scenario.model_validate_json(stripped))
    return pack, scenarios
