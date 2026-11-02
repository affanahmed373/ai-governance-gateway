# AI Governance Gateway

Reference architecture and working skeleton for a **governed enterprise AI platform**: one controlled entry point for LLM and agent access, with approved models, guardrails, audit logging, and rules drawn from the GDPR, the EU AI Act, and the OWASP Agentic Top 10 2026.

> Status: starter skeleton. The docs and control mapping are the main value; the code shows the pattern, not a finished product.

## Rules that govern the agent

Agent actions go through `POST /v1/agent/act`. The gateway denies the call unless it meets the rules in [docs/governing-rules.md](docs/governing-rules.md). Each rule is mapped to a control, a test, and evidence in [docs/control-matrix.md](docs/control-matrix.md).

- **GDPR.** Purpose must be on the agent's allow-list. Non-public data needs a declared lawful basis. Special-category data is denied. A high-impact tool cannot run without human approval. Personal data stays in an allowed region. The audit log stores a hash of the prompt, not the prompt.
- **EU AI Act.** A declared prohibited purpose is denied. A consequential tool call waits for human oversight. The response names the agent and the decision.
- **OWASP Agentic Top 10 2026 (ASI01–ASI10).** Prompt-injection check, tool allow-list, named caller, approved agents and tools only, code execution denied, memory writes need approval, peers must be allow-listed, and a step budget caps how far one action can run.

The caller declares `purpose`, `lawful_basis`, and `human_approved`. This skeleton does not detect an undeclared prohibited purpose, and it does not verify a real approval token.

## Why this exists

Enterprise teams need to use LLMs without each team re-solving security, privacy and compliance. This repo shows one way to do it:

- **Unified model gateway**: every model call goes through one API.
- **Approved model list**: provenance, license, region and data-class limits per model.
- **Guardrails**: prompt-injection detection, PII masking, output checks.
- **Audit and cost accountability**: structured logs per request (who, which model, which policy, what decision).
- **Lifecycle gates**: Dev / UAT / Prod promotion rules.
- **Traceable compliance**: the agent rules above, plus the OWASP LLM Top 10, mapped to controls, tests, and evidence.

## Architecture (high level)

```
Client / Agent
     |
     v
[ API Gateway: Entra ID auth, rate limits ]
     |
     v
[ AI Governance Gateway (FastAPI) ]
   1. Authenticate + attribute caller
   2. Policy check (approved model; for agents also purpose, tool, lawful basis, region, data class)
   3. Input guardrails (prompt injection, PII)
   4. Route to model (Azure OpenAI / on-prem)
   5. Output guardrails
   6. Audit log + telemetry
     |
     v
[ Azure OpenAI | other approved models ]
```

See [docs/architecture.md](docs/architecture.md) and [docs/azure-mapping.md](docs/azure-mapping.md).

## Repo layout

| Path | Content |
|---|---|
| `docs/architecture.md` | Components, data flow, environments |
| `docs/governing-rules.md` | GDPR, EU AI Act, and OWASP Agentic Top 10 2026 rules for the agent |
| `docs/azure-mapping.md` | Which Azure service implements which control |
| `docs/control-matrix.md` | Requirement -> control -> test -> evidence |
| `docs/threat-model.md` | Assets, threats, mitigations |
| `docs/model-onboarding.md` | Model approval workflow and checklist |
| `docs/adr/` | Architecture decision records |
| `config/approved_models.yaml` | Approved model registry (example) |
| `config/agent_policy.yaml` | Approved agents, tools, purposes, and step budget |
| `app/` | FastAPI gateway skeleton |
| `tests/` | Guardrail and policy tests |
| `infra/azure/` | Terraform skeleton for Azure |
| `.github/workflows/ci.yml` | Lint + tests as a release gate |

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest
uvicorn app.main:app --reload
```

## Roadmap

- [ ] Real Azure OpenAI client behind the router
- [ ] Entra ID token validation (JWT) and role mapping
- [ ] Langfuse tracing and per-team cost reports
- [ ] Red-team test suite (prompt injection, data leakage) in CI
- [ ] Terraform: private endpoints, Log Analytics, Defender for Cloud
- [x] Agent/tool registration and policy enforcement (`POST /v1/agent/act`; rules in [docs/governing-rules.md](docs/governing-rules.md)). Approval tokens and a code sandbox are still open.

## Disclaimer

Personal learning and portfolio project. It uses no employer code or data. Not legal advice; validate controls with your own legal and security teams.
