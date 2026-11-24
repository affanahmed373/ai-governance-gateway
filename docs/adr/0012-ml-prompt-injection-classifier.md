# ADR 0012: Pure-Python TF-IDF classifier beside injection patterns

- Status: Accepted
- Date: 2026-11-24

## Context

Roadmap item 4 asks for an ML prompt-injection classifier next to the existing regex heuristics, with precision and recall on a labelled set. Options:

1. A transformer (e.g. Hugging Face) — strong accuracy, large image and cold-start cost on Container Apps scale-to-zero.
2. scikit-learn TF-IDF + logistic regression — familiar, but adds scipy/numpy native wheels (heavier image; some Windows endpoint policies block those DLLs).
3. An external LLM judge — needs an API key and adds latency to every check.
4. A small pure-Python TF-IDF + logistic regression fitted from YAML — no native deps, fits the slim demo image, metrics are reproducible in CI.

## Decision

- Keep the regex patterns as the first gate.
- Add a pure-Python bag-of-words TF-IDF + logistic regression pipeline trained at process start from `config/prompt_injection_labels.yaml`.
- Deny when either the patterns or the ML score (default threshold 0.5) says injection. Same HTTP detail `prompt_injection_detected` / rule `prompt_injection`.
- Report precision and recall on the held-out `eval` split in CI (`test_injection_classifier_precision_recall`).
- Opt out with `GATEWAY_INJECTION_ML=0`. Tune score with `GATEWAY_INJECTION_ML_THRESHOLD`.

## Consequences

+ Catches paraphrases the regex list misses without shipping sklearn/scipy or a multi-hundred-MB model.
+ Recruiters can see an ML control and measured precision/recall in the test suite.
+ Demo image stays close to the previous size; local and CI imports stay reliable.
- Small labelled set; metrics are demo-grade, not production red-team coverage.
- Hand-rolled trainer is simpler than a production sklearn pipeline; improve labels before trusting the score alone.
