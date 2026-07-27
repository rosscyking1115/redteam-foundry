# Benchmark staleness report — advbench

- **Staleness score (heuristic):** 0.43 / 1.00
- **Interpretation:** Mixed - some staleness signals; read the component breakdown before concluding.
- **Confidence:** high (4/5 components had data)
- **Inputs:** 504 cases, 4 run(s)

> Heuristic, not a verdict. A high score flags a benchmark for review; it is not proof the corpus is worthless, nor is a low score proof a model is safe. Run components require runs that used THIS corpus.

## Components

| component | weight | score | detail |
| --- | ---: | ---: | --- |
| obsolete_pattern | 0.30 | 0.00 | 0/504 prompts match a dated jailbreak-meme marker |
| duplicate_cluster | 0.20 | 0.00 | exact-dup rate 0.0%, 5 near-dup pair(s) over 504 cases |
| universal_low_asr | 0.25 | 0.99 | max baseline ASR 1.0% across 2 baseline run(s) |
| low_defence_sensitivity | 0.15 | 0.90 | largest baseline→defence ASR shift 1.0% (ref 10%) |
| judge_disagreement | 0.10 | — | undefined - 4/4 degenerate (both judges constant, κ is 0/0) |

Scores are in [0, 1]; higher = more stale. The composite is a weight-renormalised average over the components that had data.
