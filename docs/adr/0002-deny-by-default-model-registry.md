# ADR 0002: Deny-by-default approved model registry

- Status: Accepted
- Date: 2026-10-31

## Decision
Only models listed as `approved` in the registry, in the right environment and with a sufficient data-class limit, can be called.

## Consequences
+ Reduces supply-chain and data-residency risk.
- Adds an onboarding step; mitigated by a clear checklist.
