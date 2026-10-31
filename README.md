# AI Governance Gateway

Reference architecture and working skeleton for a **governed enterprise AI platform**: one controlled entry point for LLM access with approved models, guardrails, audit logging, evaluation gates and Azure deployment.

> Status: starter skeleton. The docs and control mapping are the main value; the code shows the pattern, not a finished product.

## Why this exists

Enterprise teams need to use LLMs without each team re-solving security, privacy and compliance. This repo shows one way to do it:

- **Unified model gateway**: every model call goes through one API.
- **Approved model list**: provenance, license, region and data-class limits per model.
- **Guardrails**: prompt-injection detection, PII masking, output checks.
- **Audit and cost accountability**: structured logs per request (who, which model, which policy, what decision).
- **Lifecycle gates**: Dev / UAT / Prod promotion rules.
- **Traceable compliance**: GDPR, EU AI Act and OWASP LLM Top 10 mapped to controls, tests and evidence.

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
   2. Policy check (approved model, region, data class)
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
| `docs/azure-mapping.md` | Which Azure service implements which control |
| `docs/control-matrix.md` | Requirement -> control -> test -> evidence |
| `docs/threat-model.md` | Assets, threats, mitigations |
| `docs/model-onboarding.md` | Model approval workflow and checklist |
| `docs/adr/` | Architecture decision records |
| `config/approved_models.yaml` | Approved model registry (example) |
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
- [ ] Agent/tool registration and policy enforcement

## Disclaimer

Personal learning and portfolio project. It uses no employer code or data. Not legal advice; validate controls with your own legal and security teams.
