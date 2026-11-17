# ADR 0005: Govern A2A tasks with the agent policy

- Status: Accepted
- Date: 2026-11-17

## Context

Agents call each other with the A2A protocol (agent card and `SendMessage`), which has its own message shape. Those calls still need the same purpose, lawful-basis, data-class, region, tool, and human-approval checks as `POST /v1/agent/act`. A second policy would drift from the control matrix.

## Decision

`POST /v1/a2a` accepts an A2A JSON-RPC `SendMessage`. `params.tenant` is the target agent. Governance fields travel on `params.metadata` and are passed to `check_agent_action`. A passed task is `TASK_STATE_COMPLETED`. A failed check is `TASK_STATE_REJECTED` with the rule id. The audit record stores `caller_agent`, `target_agent`, the decision, and a hash of the message text.

## Consequences

+ One checker covers direct agent actions and agent-to-agent tasks.
+ A denial is visible as an A2A task state and as a control-matrix rule id.
- Callers must send the governance fields. The gateway does not infer purpose, lawful basis, or human approval from the message text.
- `human_approved` remains a declared flag. A verified approval token is a later decision.
