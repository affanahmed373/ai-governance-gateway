# Threat Model (summary)

## Assets

User prompts and documents, model outputs, credentials and keys, the approved model registry, audit logs.

## Trust boundaries

Client -> gateway; gateway -> model provider; gateway -> data connectors (RAG stores, tools); gateway -> log store.

## Threats and mitigations

| Threat | Example | Mitigation |
|---|---|---|
| Prompt injection | Document tells the model to ignore rules and exfiltrate data | Input heuristics, content shields, tool allow-list, output checks |
| Data leakage | PII or confidential text sent to a non-approved model | Data-class policy, PII masking, approved regions only |
| Unapproved model use | Team calls an unvetted model | Gateway allow-list; deny by default |
| Credential theft | API keys in code or logs | Managed identity, Key Vault, secret scanning in CI |
| Excessive agent permissions | Agent deletes data via a tool | Tool registration, least privilege, human approval |
| Cost abuse | Runaway token usage | Quotas, budgets, alerts |
| Log tampering | Audit trail altered | Write-once export, restricted access |
| Vendor/supply-chain risk | Model or dependency changes behavior | Version pinning, change management, re-evaluation on change |

Next step: formal STRIDE pass per component.
