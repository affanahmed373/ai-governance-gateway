# Guardrails

Input checks that run after agent and model policy, before the (stub) model call.

## Prompt injection

Two gates, OR’d together ([ADR 0012](adr/0012-ml-prompt-injection-classifier.md)):

1. **Regex heuristics** in `app/guardrails.py` (`INJECTION_PATTERNS`) — fast, exact phrases.
2. **ML classifier** in `app/injection_classifier.py` — pure-Python TF-IDF + logistic regression fitted at process start from `config/prompt_injection_labels.yaml` (no sklearn).

Either gate produces the same deny: HTTP 400 `prompt_injection_detected`, audit rule `prompt_injection`.

| Env | Meaning |
|---|---|
| `GATEWAY_INJECTION_ML` (or `gateway-injection-ml`) | `0` / `false` / `off` disables the ML gate. Default on. |
| `GATEWAY_INJECTION_ML_THRESHOLD` | Score cut-off (default `0.5`). |

CI reports precision and recall of the ML score on the held-out `eval` split (`test_injection_classifier_precision_recall`). The labelled set is small and demo-grade; raise the bar with more labels before treating it as production red-team coverage.

## PII masking

Email, phone, and IBAN patterns are replaced with `[EMAIL]`, `[PHONE]`, `[IBAN]` before the stub response. The audit log stores a SHA-256 of the prompt, not the text.
