# ADR 0004: Audit logs store metadata, not raw PII

- Status: Accepted
- Date: 2026-10-31

## Decision
Audit records contain request ID, caller, model, policy decision, token counts and a hash of the prompt. Raw prompts are not stored by default.

## Consequences
+ Supports data minimisation (GDPR).
- Debugging needs opt-in, access-controlled sampling.
