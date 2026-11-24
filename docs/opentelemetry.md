# OpenTelemetry policy spans

Short note for later. Decision: [ADR 0011](adr/0011-opentelemetry-policy-spans.md).

## Two trails, one decision

```text
POST /v1/agent/act  (or /v1/chat, /v1/a2a)
        |
        v
  write_audit()
        |
        +-- JSON line on stdout          --> compliance / Log Analytics
        |
        +-- span policy.decision         --> operators / APM
              attributes:
                governance.rule
                governance.decision
                governance.request_id
                governance.prompt_sha256
                (agent/tool/caller when present)
```

The span does **not** carry the prompt text. Same rule as the audit log.

## Config

| Env | Meaning |
|---|---|
| `OTEL_SERVICE_NAME` | Defaults to `ai-governance-gateway` |
| `OTEL_CONSOLE_EXPORTER` | `1` (default) prints spans to stderr; `0` disables |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | If set, also export via OTLP/HTTP |

## Code

| Path | Role |
|---|---|
| `app/telemetry.py` | Tracer setup + `record_policy_decision` |
| `app/main.py` | Calls setup at import; `write_audit` records the span |
| `tests/test_telemetry.py` | Asserts rule id and status on an in-memory exporter |
