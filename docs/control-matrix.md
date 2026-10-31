# Control Matrix

Maps requirements to technical controls, tests and evidence. Status values: Planned, Partial, Implemented.

| ID | Requirement (source) | Control | Test | Evidence | Status |
|---|---|---|---|---|---|
| C-01 | Lawful, minimised processing (GDPR Art. 5, 25) | PII masking before model call; data-class check | `test_pii_masking` | Audit logs, policy config | Partial |
| C-02 | Security of processing (GDPR Art. 32) | Entra ID auth, Key Vault, private endpoints, TLS | Infra review, IaC plan | Terraform plan, access logs | Planned |
| C-03 | Records of processing / accountability (GDPR Art. 5(2), 30) | Structured audit log per request | `test_audit_record_fields` | Log Analytics export | Partial |
| C-04 | Human oversight (EU AI Act Art. 14) | Approval gates for high-impact agent actions | Workflow test | Approval records | Planned |
| C-05 | Logging and traceability (EU AI Act Art. 12) | Request IDs, model version, policy decision logged | `test_audit_record_fields` | Audit logs | Partial |
| C-06 | Robustness and cybersecurity (EU AI Act Art. 15) | Red-team suite in CI, rate limits | `test_prompt_injection_*` | CI reports | Partial |
| C-07 | Prompt injection (OWASP LLM01) | Input heuristics, tool allow-list, content shields | `test_prompt_injection_*` | CI reports | Partial |
| C-08 | Sensitive information disclosure (OWASP LLM02) | PII masking in/out, output filter | `test_pii_masking` | CI reports | Partial |
| C-09 | Supply chain (OWASP LLM03) | Approved model registry with provenance and license | `test_unapproved_model_blocked` | Registry + approval records | Partial |
| C-10 | Excessive agency (OWASP LLM06) | Agent/tool registration and least privilege | Tool policy test | Registry, logs | Planned |
| C-11 | Unbounded consumption (OWASP LLM10) | Quotas and cost tracking per team | Load/limit test | Usage reports | Planned |
| C-12 | Change management | ADRs, PR reviews, environment gates | CI gate | PR history, ADRs | Partial |

For audits: each row should link to a concrete artifact (test result, log query, approval record).
