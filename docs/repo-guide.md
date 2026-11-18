# Repo guide

A map for coming back later. It says what each folder is for, how a call moves through the code, and which files the lifecycle expects you to touch.

This repository is the gate. The spice shop and the clothing store are other repositories. They do not live here. Their names appear in `config/agent_policy.yaml` so the rules have a real story. The clothing-store assistant (`multi-cloud-retail-agent`) can send every LLM call here: set `LLM_PROVIDER=gateway` and `GOVERNANCE_GATEWAY_URL` to this API. That hits `POST /v1/chat`.

## A call, file by file

A spice price check arrives at `POST /v1/agent/act`. A cloth-shop agent asking the catalog agent arrives at `POST /v1/a2a`. Both paths use the same checks.

| Step | What happens | Where |
|---|---|---|
| 1 | The HTTP route reads the body and writes the audit line | `app/main.py` |
| 2 | A2A only: turn the agent card or the `SendMessage` task into those same fields | `app/a2a.py` |
| 3 | Is this agent allowed to use this tool, for this purpose, in this region, with this data? | `app/agent_policy.py` reads `config/agent_policy.yaml` |
| 4 | Is this model approved for this environment and data class? | `app/policy.py` reads `config/approved_models.yaml` |
| 5 | Does the text look like a prompt injection? Mask email, phone, and IBAN | `app/guardrails.py` |
| 6 | Record the decision and a hash of the text. Do not record the text | `write_audit` in `app/main.py` |
| 7 | Return allow or deny. The model call is still a stub | the return value in `app/main.py` |

An A2A denial is HTTP 200 with task state `TASK_STATE_REJECTED` and the rule id. A direct agent denial is HTTP 403 with the same rule id.

The two shop stories in the README use this path. `cloth-shop-agent` may call `cloth-catalog-agent`. `cloth-catalog-agent` may not call `spice-invoice-agent`.

## Folders and files

### The running program

| Path | Purpose |
|---|---|
| `app/main.py` | The FastAPI app. Routes: `/health`, `/v1/chat`, `/v1/agent/act`, `/v1/a2a`, and the agent-card URLs. This is the front door. |
| `app/agent_policy.py` | The agent rules, in a fixed order. Returns a reason such as `human_approval_required` or `target_agent_not_allowed`. |
| `app/policy.py` | The model allow-list. Unknown or unapproved models are denied. |
| `app/guardrails.py` | Prompt-injection patterns and PII masking. |
| `app/a2a.py` | Agent cards and the A2A `SendMessage` task. It does not invent a second policy. It calls the checkers above. |
| `requirements.txt` | Python packages. CI installs this file. |

### The rules the program reads

| Path | Purpose |
|---|---|
| `config/agent_policy.yaml` | Which agents exist, what they may do, and which other agent they may call. The spice shop and the clothing store are the examples. |
| `config/approved_models.yaml` | Which models exist, where they are hosted, and how sensitive the data may be. |

Change the YAML to change who is allowed. Change the Python only when the check itself changes.

### Proof that the rules hold

| Path | Purpose |
|---|---|
| `tests/test_agent_policy.py` | Each denial reason for a direct agent action, including the spice price check. |
| `tests/test_a2a.py` | Agent cards, the cloth-shop allow, the spice-invoice deny, and the A2A audit line. |
| `tests/test_policy.py` | Model allow and deny. |
| `tests/test_guardrails.py` | Injection detection and PII masking. |
| `tests/test_audit.py` | A denied chat is logged without the raw prompt. |
| `.github/workflows/ci.yml` | On every push and pull request: install dependencies, run ruff, run pytest. |

### What you read, and what a change must update

| Path | Purpose in the lifecycle |
|---|---|
| `README.md` | The page a recruiter sees first. The allow and deny examples must still run. |
| `CHANGELOG.md` | What changed, newest first. New work goes under `Unreleased` until a version is tagged. |
| `ROADMAP.md` | What is not built yet, and what "done" means. Check an item off only when that definition is met. |
| `docs/governing-rules.md` | Why a call is denied, in the words of the GDPR, the EU AI Act, and the OWASP agent list. |
| `docs/control-matrix.md` | One row per requirement: the rule, the test name, and where the evidence lives. |
| `docs/architecture.md` | The parts and the order of a request. Also the Dev, UAT, and Prod gates. |
| `docs/threat-model.md` | What can go wrong, and which check answers it. |
| `docs/azure-mapping.md` | Which Azure service is meant to host each control. This is a plan, not a running cloud. |
| `docs/model-onboarding.md` | How a model is approved, watched, and retired. |
| `docs/adr/` | A short record when a choice would be costly to undo. ADR 0001 is "one gateway". ADR 0005 is "A2A uses the same agent policy". |
| `docs/repo-guide.md` | This file. Update it when a folder or a step in the path is added or renamed. |
| `.cursor/rules/product-lifecycle.mdc` | The instruction that a code change also updates tests, the changelog, the README, and the doc that owns the behavior. |

### Demo hosting

| Path | Purpose |
|---|---|
| `Dockerfile` | The demo image, port 7860. CI publishes it to `ghcr.io` after tests pass on `main`. |
| `infra/azure/demo/` | Terraform for the public demo: one Container App, scale to zero, Log Analytics. |
| `docs/azure-demo.md` | Deploy steps, abuse limits, new-version rollout, Log Analytics query, destroy. |
| `app/rate_limit.py` | Per-client sliding-window rate limit and prompt size helpers for the public demo. |
| `scripts/destroy-azure-demo.ps1` / `.sh` | Tear down `infra/azure/demo` so residual Azure cost stops. |
| `docs/adr/0009-public-demo-abuse-limits.md` | Why in-app limits instead of API Management for the portfolio demo. |
| `requirements-runtime.txt` | Packages installed in that image (no pytest/ruff). |
| `docs/hf-space.md` | Hugging Face steps, kept for a PRO account. Not the current host. |
| `.env.example` | Template for the Azure `ARM_*` deploy credentials and the optional `HF_TOKEN` (copy to `.env`; never commit `.env`). |
| `docs/images/denied-request.png` | Screenshot of a denied `/docs` Execute. |
| `app/demo_examples.py` | Allow/deny bodies shown in Swagger. |

### Azure, later

| Path | Purpose |
|---|---|
| `infra/azure/main.tf` | A Terraform sketch: a resource group, Log Analytics, and a managed identity. It does not deploy the gateway. |
| `infra/azure/variables.tf` | The names and location that sketch would use. |

ADR 0008 puts the public demo on Azure Container Apps with scale to zero, as ADR 0003 proposed. `infra/azure/main.tf` is the larger enterprise design (Premium registry, Key Vault) and is not applied. The admin screen should be a Next.js app on Vercel (`ROADMAP.md` item 2c).

## The lifecycle in one pass

A behavior change is finished only when all of these are true:

1. A test fails if the new behavior is lost, and `ruff` and `pytest` pass.
2. `CHANGELOG.md` has a line under `Unreleased`.
3. `README.md` still matches what a person can run, when the change is something they would try.
4. The doc that describes that behavior is updated. The table in `.cursor/rules/product-lifecycle.mdc` names which doc.
5. An ADR is added only when the approach was a real choice. A wording fix does not get one.

Leave a file alone when the change does not make it wrong.
