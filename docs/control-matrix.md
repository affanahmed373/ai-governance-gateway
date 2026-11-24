# Control Matrix

Maps requirements to technical controls, tests and evidence. Status values: Planned, Partial, Implemented.

| ID | Requirement (source) | Control | Test | Evidence | Status |
|---|---|---|---|---|---|
| C-01 | Lawful, minimised processing (GDPR Art. 5, 25) | PII masking before model call; data-class check | `test_pii_masking` | Audit logs, policy config | Partial |
| C-02 | Security of processing (GDPR Art. 32) | Entra ID auth, Key Vault, private endpoints, TLS | Infra review, IaC plan | Terraform plan, access logs | Planned |
| C-03 | Records of processing / accountability (GDPR Art. 5(2), 30) | Structured audit log per request; raw prompt is not stored | `test_agent_audit_metadata_only`, `test_a2a_audit_records_caller_and_target`, `test_cloth_shop_chat_audit_log` | Audit logs | Partial |
| C-04 | Human oversight (EU AI Act Art. 14) | High-impact tools require a signed `approval_token` from the admin queue | `test_human_approval_required`, `test_high_impact_deny_enqueues_and_token_allows_retry` | Audit logs, admin console | Implemented |
| C-05 | Logging and traceability (EU AI Act Art. 12) | Request IDs, model, agent, tool, purpose, and policy decision logged to stdout; each decision also emits an OpenTelemetry `policy.decision` span with `governance.rule` | `test_agent_audit_metadata_only`, `test_a2a_audit_records_caller_and_target`, `test_cloth_shop_chat_audit_log`, `test_audit_lines_reach_stdout`, `test_policy_decision_emits_span_with_rule_id` | Log Analytics, OTel console/OTLP | Partial |
| C-06 | Robustness and cybersecurity (EU AI Act Art. 15) | Red-team suite in CI; per-client rate limit on the public demo | `test_prompt_injection_*`, `test_rate_limit_returns_429` | CI reports, `GATEWAY_RATE_LIMIT_PER_MINUTE` | Partial |
| C-07 | Prompt injection (OWASP LLM01) | Input heuristics, tool allow-list, content shields | `test_prompt_injection_*` | CI reports | Partial |
| C-08 | Sensitive information disclosure (OWASP LLM02) | PII masking in/out, output filter | `test_pii_masking` | CI reports | Partial |
| C-09 | Supply chain (OWASP LLM03) | Approved model registry with provenance and license | `test_unapproved_model_blocked` | Registry + approval records | Partial |
| C-10 | Excessive agency (OWASP LLM06) | Agent/tool registration and least privilege | `test_tool_not_allowed` | `config/agent_policy.yaml`, logs | Partial |
| C-11 | Unbounded consumption (OWASP LLM10) | Demo request and prompt caps; max 1 replica; destroy script to stop residual cost | `test_rate_limit_returns_429`, `test_oversized_prompt_rejected` | Container App env, `scripts/destroy-azure-demo.*` | Partial |
| C-12 | Change management | ADRs, PR reviews, environment gates | CI gate | PR history, ADRs | Partial |
| C-13 | Purpose limitation (GDPR Art. 5(1)(b)) | Declared purpose must be on the agent allow-list | `test_purpose_not_allowed` | `config/agent_policy.yaml` | Implemented |
| C-14 | Lawful basis (GDPR Art. 6) | Non-public data requires a declared Art. 6(1) basis | `test_lawful_basis_required`, `test_a2a_applies_agent_rules` | Audit logs | Implemented |
| C-15 | Special-category data (GDPR Art. 9) | `restricted` data class denied for every agent | `test_special_category_denied`, `test_a2a_applies_agent_rules` | `config/agent_policy.yaml` | Implemented |
| C-16 | Automated decisions (GDPR Art. 22) | High-impact tools require a signed `approval_token` | `test_human_approval_required`, `test_a2a_human_approval_allows_task`, `test_human_approved_boolean_alone_is_not_enough` | Audit logs | Implemented |
| C-17 | International transfers (GDPR Art. 44) | Non-public data only to an allowed model region | `test_region_not_allowed`, `test_a2a_applies_agent_rules` | Model registry, agent policy | Implemented |
| C-18 | Prohibited practices (EU AI Act Art. 5) | Declared prohibited purposes denied | `test_purpose_prohibited` | `config/agent_policy.yaml` | Partial |
| C-19 | Transparency (EU AI Act Art. 13, 50) | Response names `agent_id` and `decision` | `test_allowed_agent_action_http` | API response | Partial |
| C-20 | Agent goal hijack (OWASP ASI01, 2026) | Prompt-injection check on agent actions | `test_agent_prompt_injection_http`, `test_a2a_prompt_injection_rejects_task` | CI reports | Partial |
| C-21 | Tool misuse (OWASP ASI02, 2026) | Tool must be on the agent allow-list | `test_tool_not_allowed` | `config/agent_policy.yaml` | Implemented |
| C-22 | Identity and privilege abuse (OWASP ASI03, 2026) | Anonymous caller denied | `test_caller_required` | Audit logs | Partial |
| C-23 | Agentic supply chain (OWASP ASI04, 2026) | Agent and tool must be registered; agent must be approved | `test_unapproved_agent_blocked` | `config/agent_policy.yaml` | Implemented |
| C-24 | Unexpected code execution (OWASP ASI05, 2026) | Code-execution tools denied | `test_code_execution_denied` | `config/agent_policy.yaml` | Implemented |
| C-25 | Memory and context poisoning (OWASP ASI06, 2026) | Memory writes need approval; raw prompt is not logged | `test_human_approval_required`, `test_agent_audit_metadata_only` | Audit logs | Partial |
| C-26 | Insecure inter-agent communication (OWASP ASI07, 2026) | Target agent must be an allowed peer; A2A tasks use the same check | `test_target_agent_not_allowed`, `test_two_agents_one_allowed_one_blocked`, `test_docs_examples_allow_and_deny_agent_act` | `config/agent_policy.yaml`, `/docs` deny example | Implemented |
| C-27 | Cascading failures (OWASP ASI08, 2026) | Step must stay inside the agent budget | `test_step_budget_exceeded` | `config/agent_policy.yaml` | Partial |
| C-28 | Human-agent trust exploitation (OWASP ASI09, 2026) | High-impact tools require a signed `approval_token` | `test_human_approval_allows_high_impact_tool`, `test_high_impact_deny_enqueues_and_token_allows_retry` | Audit logs, `web/` approvals page | Implemented |
| C-29 | Rogue agents (OWASP ASI10, 2026) | Unapproved agent denied | `test_unapproved_agent_blocked` | `config/agent_policy.yaml` | Implemented |

Rules and the limits of this skeleton (declared purpose, unverified approval flag): [governing-rules.md](governing-rules.md).

For audits: each row should link to a concrete artifact (test result, log query, approval record).
