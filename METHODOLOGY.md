# Methodology

> Skeleton — sections marked **TBD** are filled in as each phase lands.
> The numbers in this doc are the source of truth for any blog / portfolio /
> dashboard claim. Update this file before claiming a result anywhere else.

## 1. Goal

Quantify how much published LLM defences reduce attack success rate (ASR)
and at what cost in false-refusal rate (FRR), across published adversarial
benchmarks and a representative target LLM mix.

## 2. Corpora

| Source | Cases (post-filter) | Categories | Pinned commit | Licence |
| --- | --- | --- | --- | --- |
| AdvBench | TBD | jailbreak, harmful_content | TBD | MIT |
| JailbreakBench (JBB-Behaviors) | TBD | jailbreak, harmful_content | TBD | MIT |
| HarmBench | TBD | jailbreak, harmful_content, prompt_injection_direct | TBD | MIT |
| AgentDojo | TBD | prompt_injection_indirect, data_exfiltration | TBD | AGPL |

Categories excluded at load time per `ETHICS.md` §"Excluded categories".
Filter is verified by `tests/unit/test_exclusion_filter.py`.

## 3. Targets

| ID | Provider | Model version | Role |
| --- | --- | --- | --- |
| `claude-sonnet-4-6` | Anthropic API | `claude-sonnet-4-6` | Frontier, primary |
| `llama3.1-8b-local` | Ollama | `llama3.1:8b` (Q4) | Local, secondary |
| `meta-secalign-8b` | Local / HF | `meta-secalign-8b` | Stretch — defence-finetuned baseline |

Judge model (separate from all targets per Lesson L17):
`claude-haiku-4-5-20251001`.

## 4. Defences (composable)

Each defence wraps a `Target` and exposes the same `send()` interface.

| # | Defence | Phase | Layer |
| --- | --- | --- | --- |
| 1 | Paranoid system prompt | 3 | Prompt |
| 2 | Constitutional principles + critique-and-revise | 3 | Prompt + post |
| 3 | OpenAI Moderation pre-filter | *deferred* (no OpenAI key) | Pre |
| 4 | Llama Guard 4 12B pre-filter | 3 | Pre |
| 5 | Llama Guard 4 12B post-filter | 3 | Post |
| 6 | Spotlighting (Hines et al., 2024) | 3 | Prompt — for indirect injection |
| 7 | SecAlign-style structured-query prompting | 3 | Prompt — fenced data delimiters |

## 5. Scoring

Three layers, in order of expense:

1. **Rule-based** — refusal-keyword detector + harmful-content regex.
   Calibrated against AdvBench's known-refused subset.
2. **LLM-judge** — Claude Haiku 4.5 with a structured rubric returning
   `{ asr: 0|1, refusal: 0|1, confidence: 0..1, reasoning: str }`.
   Pinned to `claude-haiku-4-5-20251001`.
3. **Human spot-check** — 5% sample exported as CSV. Compute Cohen's kappa
   between human and judge labels. **Target: kappa > 0.6.**

## 6. Metrics reported

- **ASR** — attack success rate, per category × per defence stack
- **FRR** — false refusal rate, on a 50-prompt benign control set
- **Inter-rater agreement** — judge vs human (Cohen's kappa)
- **Cost** — USD per case, total run cost

## 7. Reproducibility guarantees

- Every model version is a **dated** ID (`claude-sonnet-4-6`, etc.).
- Every dataset is pinned to a specific commit hash.
- Every API call is cached by `(target_id, model_version, hash(messages))`.
- `pyproject.toml` + `uv.lock` pin every Python dependency.
- CI runs lint + typecheck + smoke on every PR (no real API calls).
- Nightly workflow runs the small (50-case) config against real targets and
  posts a results PR for human review before merge.

## 8. Limits (what this benchmark does not measure)

- **Multi-turn / agentic attacks** beyond AgentDojo's scope.
- **Image / vision** red-teaming — text-only for v1.
- **Closed-weight model internals** (logit-level probes, activation
  steering) — inaccessible without research partnership.
- **Production deployability** — this is a measurement tool, not a deployable
  defence layer.
- **Generalisation beyond the included benchmarks** — results characterise
  performance on these specific datasets with these specific defences. They
  are not a general "safety score."

## 9. Future work

- Integrate AgentDyn (2026 follow-up to AgentDojo) once it stabilises.
- Add OpenAI as a second frontier provider (requires OpenAI API key).
- Vision red-teaming (separate ethics + scope).
- Expand the human spot-check to 10% of cases.

## 10. Verification log

| Date | What was verified |
| --- | --- |
| 2026-05-05 | Pre-Phase-0 stack audit. Confirmed Claude 4.6/4.7 family, Llama 4 / Llama Guard 4 availability, OWASP LLM Top 10 v2025, GHA v6, Python 3.13. Added SecAlign to defence stack. Selected llama3.1:8b for local target (Llama 4 Scout requires more RAM than the dev machine has). |
| 2026-05-08 | Phase 3 defence layer landed. Six defences implemented (system-prompt, constitutional, spotlighting, secalign, llamaguard4-pre, llamaguard4-post). Exit-check live smoke asserts defences never reduce baseline refusal rate. |
