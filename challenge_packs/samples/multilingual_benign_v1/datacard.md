# Challenge pack card — multilingual_benign_v1

- **Version:** 1.0.0
- **Scenarios:** 25
- **Created:** 2026-07-01T16:47:31.973483+00:00
- **Sources:** benign_multilingual
- **Languages:** ja, ko, mixed-en-ja, mixed-en-ko, mixed-en-zh, zh-Hans, zh-Hant
- **Attack families:** —
- **Harm categories:** benign
- **Prompts redacted:** no

Benign multilingual control set (zh-Hant/zh-Hans/ja/ko + code-switch) for language-specific false-refusal testing.

## Recommended use

- benchmark_research
- release_gate_regression

## Not recommended for

- standalone_deployment_approval

## Safety notes

- Passing this pack is NOT proof of safety; it is a regression check on specific, static scenarios.
- Not a substitute for incident replay, policy-as-code gates, or a release decision — those belong in a downstream release-gate layer.
