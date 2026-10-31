# ADR 0001: Central model gateway

- Status: Accepted
- Date: 2026-10-31

## Context
Teams calling model APIs directly leads to inconsistent security, no central audit trail and uncontrolled cost.

## Decision
All model access goes through one gateway that enforces policy, guardrails and logging.

## Consequences
+ Single place for controls and evidence.
+ Easy to swap models.
- Gateway becomes critical infrastructure: needs HA and good observability.
