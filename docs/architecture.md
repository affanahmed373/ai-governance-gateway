# Architecture

## Components

- **API layer**: Azure API Management (or Container Apps ingress) with Entra ID authentication.
- **Gateway service**: FastAPI app that enforces policy, runs guardrails and routes to models.
- **Model registry**: `config/approved_models.yaml` (in production: a database or registry with an approval workflow).
- **Agent policy**: `config/agent_policy.yaml`. Approved agents, tools, purposes, peers, and step budget. Rules: [governing-rules.md](governing-rules.md).
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

## Agent action flow

`POST /v1/agent/act` applies the checks in [governing-rules.md](governing-rules.md) before the model policy and input guardrails above.

1. Agent is registered and approved for this environment.
2. Purpose is allowed and not prohibited. Non-public data has a declared lawful basis and an allowed model region. `restricted` data is denied.
3. Caller is named. The tool is allow-listed. Code execution is denied. High-impact tools need `human_approved`. The step is inside the budget. A target agent must be an allowed peer.
4. Model policy and input guardrails run.
5. The response names the agent and the decision. The audit record adds agent, tool, purpose, and rule, and still stores a prompt hash.

## Environments and gates

| Env | Purpose | Gate to promote |
|---|---|---|
| Dev | Experiments | Unit tests pass |
| UAT | Validation | Eval suite + security tests pass, review sign-off |
| Prod | Live | Approved model, ADR recorded, rollback plan, monitoring in place |

## Non-functional goals

Resilience (retries, fallback model), scalability (stateless service, autoscale), cost control (per-team budgets and usage logs), and operability (health endpoints, alerts, runbooks).
