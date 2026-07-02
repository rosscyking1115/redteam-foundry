# Roadmap — from harness to benchmark foundry

This document is the forward-looking companion to [`METHODOLOGY.md`](../METHODOLOGY.md)
(which is the source of truth for everything already *measured*). It describes
where `redteam-foundry` is going and what is — and is **not** — built yet.

## The two-layer thesis

Modern LLM safety needs two distinct things, and most projects blur them:

1. **High-quality adversarial benchmarks** — discovered, validated, scored for
   staleness, and packaged. ← *this repo*
2. **Production release gates** — incident replay, policy-as-code, ship/warn/block
   evidence. ← a separate deployment layer (`agent-release-gates`, companion project)

`redteam-foundry` is the **upstream research layer**. It does not decide
whether an agent ships; it produces audited adversarial evidence and challenge
packs that a downstream release gate can consume. See the README's
[Positioning](../README.md#positioning) section.

> **Validate the benchmark before you trust the gate.**

## Why the pivot

The v1 headline finding — published static attacks succeed 0–4% on 2026-era
models, and prompt-only defences do not move that — is itself the motivating
signal. A near-zero ASR is ambiguous: it can mean a robust model *or* a stale
benchmark, and ASR alone cannot tell them apart. Measuring that difference —
benchmark quality, staleness, defence sensitivity, multilingual robustness — is
the contribution this layer specialises in.

## What already exists (reuse, don't rebuild)

| Foundry capability | Backing code today | State |
| --- | --- | --- |
| ASR / defence measurement with bootstrap CIs | `orchestrator.py`, `stats.py` | shipped |
| Judge reliability (cross-judge κ / Krippendorff α) | `scorers/`, `orchestrator.py` | shipped |
| Corpus loaders + safety exclusion filter | `corpora/`, `corpora/_filters.py` | shipped |
| 6 composable defences | `defences/` | shipped |
| Inspect AI eval-log export | `inspect_export.py` | shipped |
| Ethics posture + redaction | `ETHICS.md`, exclusion-filter tests | shipped |

## Phased plan

Each phase is one PR with green CI. Phase 0 is complete.

### Phase 0 — Stabilise & re-anchor — **done**
- Closed three exclusion-filter leaks (WMD "synthesis" noun, self-harm
  phrasings, case-insensitive category gate) + regression tests.
- Correctness fixes: Krippendorff α finite-sample correction, `compute_kappa`
  blank-cell guard, cross-judge `None`-vs-`0.0`.
- **0b:** this positioning/roadmap pass.

### Phase 1 — Corpus quality layer — **done** (1a + 1b)
- Exact + near-duplicate detection, **cross-corpus**; composition, prompt-length,
  label-integrity checks. `redteam corpora audit` → quality report + data card.
- Language/script coverage (code-switching flag) + attack-family surface markers.

### Phase 2 — Staleness & usefulness — **done**
- `redteam corpora staleness` composes corpus signals (obsolete-meme patterns,
  duplication) with run signals (universal-low-ASR, defence-insensitivity,
  judge-disagreement) into a **heuristic**, component-broken-out `staleness_score`
  — never a single magic number, renormalised over whatever data is available.
- Worked example: AgentDojo scores ~0.43 ("mixed") — driven by near-universal
  attack failure and low defence sensitivity, while cross-judge κ=+1.000 confirms
  ASR itself is well-posed.

### Phase 3 — Defence comparison + safe-usefulness — **done**
- Committed **benign control set** (`redteam.benign`, ~45 prompts incl.
  sensitive-but-legitimate over-block stressors); runnable via
  `configs/run_benign_control_*.yaml` to measure false-refusal rate (FRR).
- `redteam compare-defences` matches adversarial + benign runs per config and
  reports ASR, FRR, `safe_usefulness = (1 - ASR) * (1 - FRR)`, cost, latency.
- Still TODO here: an actual benign run set (needs live API/Ollama) to populate
  FRR on the published matrix.

### Phase 4 — Multilingual corpus *(distinctive contribution)* — **done**
- `redteam.multilingual`: benign control set in zh-Hant / zh-Hans / ja / ko +
  code-switched prompts, each with a precise `lang` tag. `redteam frr-by-language`
  reports false-refusal broken down by language (exact via recorded `lang`,
  distinguishing Hant/Hans; else script-detected).
- **Ethics boundary (see ETHICS.md):** benign-only. We do not translate harmful
  prompts into other languages — that would create harmful content and bypass
  the English-only exclusion filter. The contribution is over-refusal
  measurement, not non-English attack generation.
- Deferred: multilingual judge-reliability (needs live judge runs).

### Phase 5 — Challenge-pack exporter — **done**
- `redteam export-pack` writes `pack.yaml` + `scenarios.jsonl` + `datacard.md`.
  Benign scenarios ship in full; **adversarial scenarios are redacted by default**
  (SHA-256 + preview, no raw harmful text) — downstream re-materialises them from
  the pinned corpus. `--include-adversarial-prompts` overrides for trusted use.
- Every pack carries `safety_notes` ("passing is not proof of safety"),
  `recommended_use`, and `not_recommended_for`. Export only — **no**
  release-decision logic here.
- Committed sample: `challenge_packs/samples/multilingual_benign_v1/`.

### Phase 6 — Bridge to a release-gate layer — **repo-side done**
- `redteam.packs.read_challenge_pack` — the inverse of the exporter, so a
  consumer can load a pack as a regression suite (round-trip tested against the
  committed sample).
- `examples/export_to_agent_release_gates.md` — the export/consume **contract**:
  pack format, how a gate turns scenarios into checks, and what it must NOT infer
  ("passing is not proof of safety"; re-materialise redacted prompts from the
  pinned corpus).
- **Deliberately no live integration.** `agent-release-gates` is a companion
  project that isn't built here; wiring an actual end-to-end gate is out of scope
  until that repo exists. This side of the bridge stands on its own.

## Follow-up hardening (from the Phase-0 review)

Done:

- ~~Budget reservation under concurrency~~ — `check_can_spend` now reserves its
  estimate; `record_spend`/`release` unwind it, so concurrent calls can't
  collectively blow the per-run cap.
- ~~Llama Guard should fail **closed**~~ — only a clean `safe` verdict passes;
  empty/errored/garbled output is treated as unsafe.
- ~~OpenAI adapter runs un-metered~~ — the target now fails loud at construction
  if its model has no pricing entry (no silent $0 / budget bypass).
- ~~Delimiter-escaping in spotlighting / SecAlign~~ — untrusted content has the
  defence's own fence markers neutralised; SecAlign's `<DATA>` passthrough
  bypass is removed.

Still open:

- Judge cache-hit cost-reporting semantics (a cache re-score re-adds the cached
  cost to reported judge spend; debatable whether that's wrong).

## Out of scope (belongs in the release-gate layer)

Production release dashboards; ship/warn/block logic; deployment approval
workflows; policy-as-code gates; CI release blocking; full incident-replay
dashboard; release audit packs.
