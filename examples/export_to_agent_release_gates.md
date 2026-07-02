# Bridge: exporting challenge packs to a release-gate layer

This document is the **contract** between this repository (the upstream
benchmark foundry) and a downstream **release-gate layer** such as the companion
project `agent-release-gates`. It defines what a challenge pack is, how a
consumer reads it, and — just as importantly — what a consumer must **not**
infer from it.

> [!NOTE]
> `agent-release-gates` is a companion project. This file documents the
> export/consume interface so the two layers stay decoupled; it does **not**
> ship a live integration, and nothing here makes a release decision. The pack
> reader below (`redteam.packs.read_challenge_pack`) is real and tested.

## The two-layer workflow

```
  redteam-foundry (this repo)                 a release-gate layer
  ───────────────────────────────                 ─────────────────────
  audit → validate → score staleness              read pack.yaml + scenarios
  → export-pack  ────────────────────►  pack/  ─► turn scenarios into
                                                  regression checks →
                                                  ship / warn / block
```

The foundry decides **which scenarios are worth testing** and packages them.
The gate decides **whether an agent may ship**. Neither reaches into the other.

## Producing a pack

```bash
# A safe, redacted adversarial pack (raw prompts are NOT included):
redteam export-pack --pack-id prompt-injection-basic --only agentdojo --limit 50

# A fully-benign pack (prompts included) — e.g. for multilingual over-refusal:
redteam export-pack --pack-id multilingual-benign --only benign_multilingual
```

Each pack is a directory:

```
<pack_id>/
  pack.yaml         # metadata (see schema below)
  scenarios.jsonl   # one Scenario per line
  datacard.md       # human-readable card
```

A committed, fully-benign example lives at
[`challenge_packs/samples/multilingual_benign_v1/`](../challenge_packs/samples/multilingual_benign_v1/).

## pack.yaml (metadata)

```yaml
pack_id: multilingual_benign_v1
version: 1.0.0
description: ...
created_at: 2026-07-01T...Z
n_scenarios: 25
sources: [benign_multilingual]
languages: [ja, ko, zh-Hans, zh-Hant, mixed-en-zh, ...]
attack_families: [instruction_override, ...]   # inferred; may be empty
harm_categories: [benign]
scenarios_redacted: false            # true if any adversarial prompt was redacted
recommended_use: [benchmark_research, release_gate_regression]
not_recommended_for: [standalone_deployment_approval]
safety_notes:
  - Passing this pack is NOT proof of safety; it is a regression check on ...
```

## scenarios.jsonl (one Scenario per line)

```json
{
  "id": "…",
  "source": "agentdojo",
  "category": "prompt_injection_indirect",
  "severity": "high",
  "lang": "en",
  "attack_families": ["instruction_override"],
  "expected_behaviour": "refuse",
  "prompt": null,                          // null when redacted
  "prompt_sha256": "8a8c7777…",
  "prompt_preview": "Write a script that can exploit vulnerab…"
}
```

- `expected_behaviour` is the assertion target: `refuse` (adversarial),
  `complete_safely` (benign), or `flag`.
- `prompt` is `null` for redacted adversarial scenarios. A consumer
  **re-materialises** the full prompt from the pinned upstream corpus (via this
  harness's loaders, keyed by `id` / verified against `prompt_sha256`) — this
  repo never re-hosts raw harmful prompts.

## Consuming a pack

The reader is the inverse of the exporter and lives in this repo, so a consumer
can depend on it directly or reimplement the (trivial) format:

```python
from pathlib import Path
from redteam.packs import read_challenge_pack

pack, scenarios = read_challenge_pack(Path("challenge_packs/samples/multilingual_benign_v1"))

for s in scenarios:
    # A release gate turns each scenario into a regression check:
    #   - benign  (expected_behaviour == "complete_safely") -> assert NOT refused
    #   - adversarial (expected_behaviour == "refuse")       -> assert refused / blocked
    # Redacted prompts are re-materialised from the pinned corpus by id.
    should_refuse = s.expected_behaviour == "refuse"
    ...
```

## What a consumer must not infer

> [!IMPORTANT]
> - **Passing a pack is not proof of safety.** It is a regression check on
>   specific, static scenarios (see each pack's `safety_notes`).
> - Packs in `not_recommended_for: [standalone_deployment_approval]` must not be
>   the sole basis for a ship decision.
> - A high pass rate on a **stale** pack (see `redteam corpora staleness`) is
>   weak evidence — validate the benchmark before you trust the gate.

## Versioning

`pack_id` + `version` identify a pack. Bump `version` when scenarios change so a
downstream gate can pin a known pack and detect drift. The upstream corpora
themselves are commit-pinned in `configs/dataset_versions.yaml`.
