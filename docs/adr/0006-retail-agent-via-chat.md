# ADR 0006: Cloth-shop LLM calls enter at `/v1/chat`

- Status: Accepted
- Date: 2026-11-17

## Context

`multi-cloud-retail-agent` already has several LLM providers. It needs a governed path for model access without rewriting its LangGraph pipeline. The gateway already exposes `POST /v1/chat` for model allow-list, prompt-injection, PII masking, and audit.

## Decision

The retail agent adds an `LLM_PROVIDER=gateway` provider that posts every `generate()` call to this gateway's `POST /v1/chat`. The caller is `cloth-shop-agent`. The gateway remains the compliance record. The model answer may still be a stub until a real backend sits behind the gateway.

## Consequences

+ Shop traffic and governance stay in separate repos.
+ Recruiters can start the gateway, set `LLM_PROVIDER=gateway`, and see an audit line.
- Answers through the gateway are stubs until Azure OpenAI (or another approved model) is wired behind `/v1/chat`.
- Agent-tool checks stay on `/v1/agent/act` and `/v1/a2a`; chat is model governance only.
