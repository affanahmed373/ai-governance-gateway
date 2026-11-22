# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions below are the product history. Git tags start at the next release.

Promotion from Dev to UAT to Prod is described in [docs/architecture.md](docs/architecture.md). Model onboarding and retirement are in [docs/model-onboarding.md](docs/model-onboarding.md).

## [Unreleased]

### Added

- TypeScript admin console in `web/` (Next.js): approval queue, audit viewer, approved-model list, and policy playground. High-impact tools now need a signed `approval_token` from `POST /v1/admin/approvals/{id}/approve` instead of a declared `human_approved` flag ([ADR 0010](docs/adr/0010-signed-approval-tokens.md), [docs/admin-console.md](docs/admin-console.md)).
- Admin API under `/v1/admin/*` (header `X-Admin-Token`): pending approvals, recent audit ring, models, and `POST /v1/admin/explain` rule checklist. CORS origins via `GATEWAY_CORS_ORIGINS`.
- CI job `web`: OpenAPI typegen, typecheck, Vitest, and one Playwright smoke test.
- Public-demo abuse limits: 30 requests/minute per client (HTTP 429), 4000-character prompt cap, Container App max 1 replica with HTTP concurrency 10. Env: `GATEWAY_RATE_LIMIT_PER_MINUTE`, `GATEWAY_MAX_PROMPT_CHARS`. See [ADR 0009](docs/adr/0009-public-demo-abuse-limits.md).
- Destroy scripts for the Azure demo stack: `scripts/destroy-azure-demo.ps1` and `scripts/destroy-azure-demo.sh`.
- Public demo on Azure Container Apps: `infra/azure/demo/` deploys one Container App that scales to zero and pulls the image CI publishes to `ghcr.io` after tests pass on `main`. Container logs go to Log Analytics. See [ADR 0008](docs/adr/0008-azure-container-apps-demo.md) and [docs/azure-demo.md](docs/azure-demo.md).
- `.env.example` with the Azure `ARM_*` credentials Terraform needs for the demo deploy, plus the optional Hugging Face token (`HF_TOKEN`); `.env` stays gitignored. Docs note that Docker Spaces on free CPU currently need Hugging Face PRO; local Docker on port 7860 is the free demo path.
- Public demo path: `Dockerfile` serves the API on port 7860; `/` redirects to `/docs`. Ready allow and deny examples on `POST /v1/agent/act` and `POST /v1/a2a` (deny rule `target_agent_not_allowed`). README Try it section with a denied-request screenshot. See [ADR 0007](docs/adr/0007-huggingface-docker-demo.md) and [docs/hf-space.md](docs/hf-space.md).
- Cloth-shop LLM path: `multi-cloud-retail-agent` can set `LLM_PROVIDER=gateway` so every `generate()` is `POST /v1/chat`. The README shows the audit line (caller `cloth-shop-agent`, decision, prompt hash). See [ADR 0006](docs/adr/0006-retail-agent-via-chat.md).
- `test_cloth_shop_chat_audit_log` for that chat audit record.
- [docs/repo-guide.md](docs/repo-guide.md): a map of the folders, the path a call takes, and which files a change updates.
- Project rule that a change is unfinished until tests are updated and the ruff and pytest gate passes, and until the changelog, README, owning docs, and any architecture decision record match the change.
- [ADR 0005](docs/adr/0005-govern-a2a-with-agent-policy.md): A2A tasks use `check_agent_action`. A denial is `TASK_STATE_REJECTED` with the rule id.
- A2A JSON-RPC `SendMessage` on `POST /v1/a2a`. Agent cards at `GET /.well-known/agent-card.json` and `GET /v1/a2a/agents/{agent_id}/agent-card.json` (protocol binding `JSONRPC`, version `1.0`).
- Each A2A task runs `check_agent_action` (data class, lawful basis, region, human approval, peer allow-list) and then the existing model and prompt-injection checks.
- A passed task is `TASK_STATE_COMPLETED`. A failed check is `TASK_STATE_REJECTED` with the rule id on `result.task.metadata.rule`.
- Audit records for A2A tasks include `caller_agent`, `target_agent`, and the decision. The message text is stored as a SHA-256 hash.
- Example agents are the spice shop and the clothing store. `spice-invoice-agent` may compare supplier prices and cannot delete an invoice without a person. `cloth-shop-agent` may ask `cloth-catalog-agent` to draft a caption. The catalog agent cannot read spice invoices (`target_agent_not_allowed`), and `publish_catalog` needs human approval.
- `tests/test_a2a.py`, including `test_two_agents_one_allowed_one_blocked`.

### Changed

- `human_approved: true` alone no longer unlocks high-impact tools. A verified `approval_token` is required (A2A metadata field `approval_token` too).

### Fixed

- Audit records were dropped when the gateway ran under `uvicorn` or in a container, because the `audit` logger had no handler and Python discards `INFO` records by default. The logger now writes its JSON lines to stdout, where container log collectors such as Log Analytics pick them up.

## [0.2.0] - 2026-11-02

### Added

- `POST /v1/agent/act`. The gateway denies the call unless the agent is approved, the purpose is allowed, non-public data has a lawful basis, the data class and model region are allowed, the caller is named, the tool is allow-listed, code execution is off, high-impact tools have `human_approved`, the step is inside the budget, and the target agent is an allowed peer.
- Rules mapped to the GDPR, the EU AI Act, and the OWASP Agentic Top 10 2026, with a row in [docs/control-matrix.md](docs/control-matrix.md) for each denial reason.
- `config/agent_policy.yaml` and `tests/test_agent_policy.py`.

## [0.1.0] - 2026-10-31

### Added

- FastAPI gateway with `GET /health` and `POST /v1/chat`. Unapproved models are denied. Prompts are checked for injection and PII is masked before the stub model call.
- Approved-model registry (`config/approved_models.yaml`) with deny-by-default access by environment and data class.
- Audit log of caller, model, environment, data class, decision, and a SHA-256 of the prompt. Raw prompts are not stored.
- Architecture, Azure mapping, control matrix, threat model, model-onboarding checklist, and ADRs.
- Terraform skeleton for Azure and a CI workflow that runs ruff and pytest.
- MIT license.
