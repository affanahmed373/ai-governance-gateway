# Architecture

## Components

- **API layer**: Azure API Management (or Container Apps ingress) with Entra ID authentication.
- **Gateway service**: FastAPI app that enforces policy, runs guardrails and routes to models.
- **Model registry**: `config/approved_models.yaml` (in production: a database or registry with an approval workflow).
- **Agent policy**: `config/agent_policy.yaml`. Approved agents, tools, purposes, peers, and step budget. Rules: [governing-rules.md](governing-rules.md). The same policy governs A2A tasks on `POST /v1/a2a`.
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

`multi-cloud-retail-agent` uses this path when `LLM_PROVIDER=gateway`: every LLM `generate()` is `POST /v1/chat` with caller `cloth-shop-agent`. Decision: [ADR 0006](adr/0006-retail-agent-via-chat.md).

The public demo image listens on port 7860 and opens on `/docs` with allow/deny examples. It runs on Azure Container Apps with `min_replicas = 0`, pulls its image from `ghcr.io`, and sends stdout, including the audit JSON lines, to Log Analytics. The open demo caps clients at 30 requests/minute and 4000 prompt characters ([ADR 0009](adr/0009-public-demo-abuse-limits.md)). Decision: [ADR 0008](adr/0008-azure-container-apps-demo.md), which supersedes the Hugging Face choice in ADR 0007.

## Agent action flow

`POST /v1/agent/act` applies the checks in [governing-rules.md](governing-rules.md) before the model policy and input guardrails above.

1. Agent is registered and approved for this environment.
2. Purpose is allowed and not prohibited. Non-public data has a declared lawful basis and an allowed model region. `restricted` data is denied.
3. Caller is named. The tool is allow-listed. Code execution is denied. High-impact tools need `human_approved`. The step is inside the budget. A target agent must be an allowed peer.
4. Model policy and input guardrails run.
5. The response names the agent and the decision. The audit record adds agent, tool, purpose, and rule, and still stores a prompt hash.

## A2A task flow

`POST /v1/a2a` accepts an A2A JSON-RPC `SendMessage`. `params.tenant` is the target agent. Metadata carries the caller agent and the same governance fields as an agent action. The gateway runs the agent-action checks, then the model policy and input guardrails. The response is a task in `TASK_STATE_COMPLETED` or `TASK_STATE_REJECTED`. The audit record adds `caller_agent` and `target_agent`. Decision: [ADR 0005](adr/0005-govern-a2a-with-agent-policy.md).

Agent cards are published at `/.well-known/agent-card.json` (the gateway) and `/v1/a2a/agents/{agent_id}/agent-card.json` (one registered agent).

## Environments and gates

| Env | Purpose | Gate to promote |
|---|---|---|
| Dev | Experiments | Unit tests pass |
| UAT | Validation | Eval suite + security tests pass, review sign-off |
| Prod | Live | Approved model, ADR recorded, rollback plan, monitoring in place |

## Non-functional goals

Resilience (retries, fallback model), scalability (stateless service, autoscale), cost control (per-team budgets and usage logs), and operability (health endpoints, alerts, runbooks).
