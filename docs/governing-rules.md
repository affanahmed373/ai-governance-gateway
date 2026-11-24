# Governing rules for the agent

Rules that bind an agent action through `POST /v1/agent/act`, and an A2A task through `POST /v1/a2a`. This is a control mapping for the skeleton, not legal advice. Validate it with your own legal and security teams.

The gateway decides from fields the caller declares (`purpose`, `lawful_basis`, `tool`, `target_agent`, and for high-impact tools a signed `approval_token`). It does not detect an undeclared prohibited purpose. The boolean `human_approved` is accepted on the wire for older clients but is not trusted; see [ADR 0010](adr/0010-signed-approval-tokens.md).

Config: `config/agent_policy.yaml`. Checker: `app/agent_policy.py`.

## GDPR

| Source | Obligation | Gateway behavior | Denial reason |
|---|---|---|---|
| Art. 5(1)(b) | Process personal data only for a specified purpose | `purpose` must be on that agent's allow-list | `purpose_not_allowed` |
| Art. 5(1)(c), Art. 25 | Minimise personal data, by design and by default | PII is masked before the model call. Audit stores a hash, not the prompt | — |
| Art. 6 | Non-public processing needs a lawful basis | `data_class` other than `public` requires one of the six Art. 6(1) bases | `lawful_basis_required` |
| Art. 9 | Special-category data needs a narrow exception | `data_class: restricted` is denied for every agent | `special_category_denied` |
| Art. 22 | No solely automated decision with legal or similar significant effect | A tool marked `requires_human_approval` is denied unless a valid `approval_token` is presented | `human_approval_required` |
| Art. 30, Art. 5(2) | Keep a record of processing | Each action writes an audit record: caller, agent, tool, purpose, decision, prompt hash | — |
| Art. 32 | Secure the processing | Same platform controls as the chat path (identity, secrets, network). Not enforced in this process | — |
| Art. 44 | Personal data stays in an adequate transfer path | Non-public data may only go to a model in `westeurope`, `northeurope`, or `on-prem` | `region_not_allowed` |

The declared lawful bases are `consent`, `contract`, `legal_obligation`, `vital_interests`, `public_task`, and `legitimate_interests`.

## EU AI Act

| Source | Obligation | Gateway behavior | Denial reason |
|---|---|---|---|
| Art. 5 | Some practices are prohibited | A declared prohibited purpose is denied even if an agent lists it | `purpose_prohibited` |
| Art. 12 | High-risk systems keep automatic logs | The audit record is the log for the action | — |
| Art. 13, Art. 50 | People can tell that an AI system is acting and what it decided | The response includes `agent_id` and `decision` | — |
| Art. 14 | Human oversight can stop a consequential action | Same approval gate as GDPR Art. 22. The admin console mints a verified token | `human_approval_required` |
| Art. 15 | Systems must be robust against attacks | Prompt-injection check on the agent prompt (regex heuristics plus TF-IDF classifier), plus the tool and step limits below | `prompt_injection_detected` (HTTP 400) |

Prohibited purposes in this skeleton: `social_scoring`, `untargeted_biometric_scraping`, `subliminal_manipulation`, `emotion_recognition_workplace`.

## OWASP Top 10 for Agentic Applications 2026

Source: [OWASP Top 10 for Agentic Applications for 2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/).

| ID | Risk | Gateway behavior | Denial reason |
|---|---|---|---|
| ASI01 | Agent goal hijack | Same prompt-injection gates as the chat path (regex + ML; [docs/guardrails.md](guardrails.md)) | HTTP 400 `prompt_injection_detected` |
| ASI02 | Tool misuse | The tool must be on that agent's allow-list | `tool_not_allowed` |
| ASI03 | Identity and privilege abuse | `caller` must be present and must not be `anonymous` | `caller_required` |
| ASI04 | Agentic supply chain | Agent and tool must be registered. Agent `status` must be `approved` | `agent_not_registered`, `agent_not_approved`, `tool_not_registered` |
| ASI05 | Unexpected code execution | A tool with `allows_code_execution` is denied even if it is on the allow-list. There is no sandbox here | `code_execution_denied` |
| ASI06 | Memory and context poisoning | `write_memory` requires human approval. Raw prompt text is not written to the audit log | `human_approval_required` |
| ASI07 | Insecure inter-agent communication | `target_agent`, when set, must be an allowed peer | `target_agent_not_allowed` |
| ASI08 | Cascading failures | `step` must be from 1 through the agent's `max_steps` | `step_budget_exceeded` |
| ASI09 | Human-agent trust exploitation | High-impact tools (`delete_invoice`, `write_memory`, `publish_catalog`, …) require a signed `approval_token` | `human_approval_required` |
| ASI10 | Rogue agents | An agent whose status is not `approved` cannot act | `agent_not_approved` |

## Check order

1. Agent is registered and approved, and the environment is allowed.
2. Purpose is not prohibited, then it is on the agent allow-list.
3. Data class is known. Non-public data has a lawful basis. `restricted` is denied. The class is within the agent's maximum.
4. Caller is named. Tool is allow-listed and registered. Code execution is denied. High-impact tools need approval.
5. Step is inside the budget. A target agent is an allowed peer. Non-public data uses an allowed model region.
6. The existing model policy, prompt-injection check (regex + ML), and PII mask then run.

Policy denials on `POST /v1/agent/act` return HTTP 403 with the reason above. The chat path is unchanged.

## A2A tasks

`POST /v1/a2a` accepts an [A2A](https://a2a-protocol.org/latest/specification/) JSON-RPC `SendMessage`. `params.tenant` is the target agent (`metadata.target_agent` is used when `tenant` is empty). The message text is the prompt. Governance fields travel on `params.metadata` and map onto `check_agent_action`:

| Metadata field | Policy field |
|---|---|
| `caller_agent` | `agent_id` |
| `tenant` or `target_agent` | `target_agent` |
| `tool`, `model`, `purpose`, `lawful_basis`, `data_class`, `caller`, `human_approved`, `step`, `environment` | the same fields |

The check order above still applies. A passed task is `TASK_STATE_COMPLETED`. A failed check is `TASK_STATE_REJECTED` with the rule id in `result.task.metadata.rule` and in the audit record. The HTTP status stays 200. The audit record stores `caller_agent`, `target_agent`, the decision, and a hash of the message text.

`cloth-shop-agent` may call `cloth-catalog-agent`. `cloth-catalog-agent` has no peers, so its call to `spice-invoice-agent` is rejected with `target_agent_not_allowed`. The spice invoice agent likewise has no peers.

Agent cards: `GET /.well-known/agent-card.json` for the gateway, and `GET /v1/a2a/agents/{agent_id}/agent-card.json` for one registered agent. The card's interface uses protocol binding `JSONRPC` and protocol version `1.0`.
