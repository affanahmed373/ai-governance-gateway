# Threat Model (summary)

## Assets

User prompts and documents, model outputs, credentials and keys, the approved model registry, the agent and tool registry, audit logs.

## Trust boundaries

Client -> gateway; gateway -> model provider; gateway -> data connectors (RAG stores, tools); gateway -> log store.

## Threats and mitigations

| Threat | Example | Mitigation | OWASP 2026 |
|---|---|---|---|
| Prompt injection | Document tells the model to ignore rules and exfiltrate data | Regex heuristics plus TF-IDF classifier, tool allow-list, output checks ([docs/guardrails.md](guardrails.md)) | ASI01 |
| Data leakage | PII or confidential text sent to a non-approved model, or written into agent memory | Data-class policy, PII masking, approved regions, approval before memory writes | ASI06 |
| Unapproved model use | Team calls an unvetted model or an unapproved agent | Gateway allow-list; deny by default | ASI04, ASI10 |
| Credential theft | API keys in code or logs; agent acts as anonymous | Managed identity, Key Vault, secret scanning in CI, named caller required | ASI03 |
| Excessive agent permissions | Agent deletes data via a tool | Tool registration, least privilege, signed approval token from the admin queue | ASI02, ASI09 |
| Unexpected code execution | Agent runs attacker-supplied code through a tool | Code-execution tools denied until a sandbox exists | ASI05 |
| Untrusted agent message | A spoofed peer tells the agent to act, including over A2A | Target agent must be an allowed peer | ASI07 |
| Cascading agent actions | One bad step fans out across a long tool loop | Per-agent step budget | ASI08 |
| Cost abuse | Runaway token usage or open-demo scraping | Per-client rate limit, prompt size cap, max 1 replica, HTTP concurrency 10, scale to zero, destroy scripts | — |
| Log tampering | Audit trail altered | Write-once export, restricted access | — |
| Vendor/supply-chain risk | Model, tool, or dependency changes behavior | Version pinning, registered agents and tools, re-evaluation on change | ASI04 |

Next step: formal STRIDE pass per component.
