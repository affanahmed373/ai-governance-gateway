# Architecture

## Components

- **API layer**: Azure API Management (or Container Apps ingress) with Entra ID authentication.
- **Gateway service**: FastAPI app that enforces policy, runs guardrails and routes to models.
- **Model registry**: `config/approved_models.yaml` (in production: a database or registry with an approval workflow).
- **Model backends**: Azure OpenAI (primary), optional on-prem models for restricted data.
- **Observability**: structured audit logs to Log Analytics; traces and cost to Langfuse.
- **Secrets**: Azure Key Vault, accessed via managed identity.

## Request flow

1. Caller presents an Entra ID token. Gateway extracts identity, team and environment.
2. Policy engine checks: model is approved, allowed in this environment, allowed for the data class, and hosted in an allowed region.
3. Input guardrails: prompt-injection heuristics, PII masking.
4. Request is routed to the backend model.
5. Output guardrails: PII leakage and policy checks.
6. Audit record is written (no raw PII; hashes and metadata).

## Environments and gates

| Env | Purpose | Gate to promote |
|---|---|---|
| Dev | Experiments | Unit tests pass |
| UAT | Validation | Eval suite + security tests pass, review sign-off |
| Prod | Live | Approved model, ADR recorded, rollback plan, monitoring in place |

## Non-functional goals

Resilience (retries, fallback model), scalability (stateless service, autoscale), cost control (per-team budgets and usage logs), and operability (health endpoints, alerts, runbooks).
