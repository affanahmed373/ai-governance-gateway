# ADR 0009: Abuse limits on the public demo API

- Status: Accepted
- Date: 2026-11-18

## Context

The public demo has no API key so recruiters can open `/docs` and run allow/deny examples. The repo is public and the Container App is on the open internet. Without caps, a scraper or misconfigured client could keep a replica warm and inflate Log Analytics ingest. Azure API Management would also rate-limit, but that is the enterprise front door and is not part of the cheap demo stack.

## Decision

- In-process sliding-window limit: 30 requests per minute per client IP (`GATEWAY_RATE_LIMIT_PER_MINUTE`), returning HTTP 429 with `Retry-After`. `/health`, OpenAPI UI, and agent cards are exempt.
- Prompt size cap: 4000 characters (`GATEWAY_MAX_PROMPT_CHARS`) on `/v1/chat`, `/v1/agent/act`, and A2A message text.
- Infra: one replica max, HTTP concurrency scale rule of 10, rate-limit env vars set on the Container App. Destroy scripts remove the whole stack when the demo is not needed.

## Consequences

+ Limits ship in the same image as the API; no extra Azure service for the portfolio demo.
+ Control matrix C-06 / C-11 move from Planned toward Partial with a concrete test.
- Per-replica in-memory counters reset on scale-to-zero cold start; they are a demo brake, not a multi-instance quota.
- A later APIM front door can replace or wrap these limits without changing the policy engine.
