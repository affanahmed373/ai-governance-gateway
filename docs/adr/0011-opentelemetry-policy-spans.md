# ADR 0011: OpenTelemetry spans alongside the JSON audit log

- Status: Accepted
- Date: 2026-11-24

## Context

Roadmap item 3 needs an OpenTelemetry trail for recruiters and operators. The gateway already writes a JSON audit line per decision (stdout / Log Analytics). Replacing that with spans alone would break the compliance evidence column in the control matrix. Shipping a full collector (Jaeger/App Insights) in the cheap demo stack would raise cost and ops load.

## Decision

- Keep the JSON audit log as the compliance record (hash of prompt, rule id, decision).
- On every `write_audit`, also emit an OpenTelemetry span named `policy.decision` with attributes `governance.rule`, `governance.decision`, caller/agent/tool metadata, and `governance.prompt_sha256` — never the raw prompt.
- Default exporter: console (visible in Container App logs). Optional `OTEL_EXPORTER_OTLP_ENDPOINT` for a real backend. `OTEL_CONSOLE_EXPORTER=0` turns the console exporter off.

## Consequences

+ Portfolio demos show spans without extra Azure services.
+ APM backends can be wired later via one env var.
- Console span output is verbose next to audit JSON; disable console export in noisy environments.
- Spans are best-effort observability; auditors should still use the JSON audit line.
