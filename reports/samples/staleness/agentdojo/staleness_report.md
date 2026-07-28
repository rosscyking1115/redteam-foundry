# Benchmark staleness report — agentdojo

- **Staleness score (heuristic):** 0.43 / 1.00
- **Interpretation:** Mixed - some staleness signals; read the component breakdown before concluding.
- **Confidence:** high (5/5 components had data)
- **Inputs:** 949 cases, 8 run(s)

> Heuristic, not a verdict. A high score flags a benchmark for review; it is not proof the corpus is worthless, nor is a low score proof a model is safe. Run components require runs that used THIS corpus.

## Components

| component | weight | score | detail |
| --- | ---: | ---: | --- |
| obsolete_pattern | 0.30 | 0.00 | 0/949 prompts match a dated jailbreak-meme marker |
| duplicate_cluster | 0.20 | 0.50 | exact-dup rate 0.0%, 6038 near-dup pair(s) over 949 cases |
| universal_low_asr | 0.25 | 0.96 | max baseline ASR 4.0% across 2 baseline run(s) |
| low_defence_sensitivity | 0.15 | 0.60 | largest baseline→defence ASR shift 4.0% (ref 10%) |
| judge_disagreement | 0.10 | 0.00 | mean cross-judge ASR κ +1.000 over 1 informative run(s); 7/8 degenerate (both judges constant, κ is 0/0) |

Scores are in [0, 1]; higher = more stale. The composite is a weight-renormalised average over the components that had data.
