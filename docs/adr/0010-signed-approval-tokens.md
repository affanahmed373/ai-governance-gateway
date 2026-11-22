# ADR 0010: Signed approval tokens instead of a boolean flag

- Status: Accepted
- Date: 2026-11-22

## Context

Roadmap 2c needs a human approval step that is enforced, not declared. Callers used to set `human_approved: true` on `POST /v1/agent/act`. That proves nothing: any client can send the flag. A separate admin console on Vercel must mint something the gateway can verify.

## Decision

- High-impact tools require an HMAC-SHA256 `approval_token` bound to `agent_id`, `tool`, `purpose`, `caller`, and an expiry.
- When a call is denied with `human_approval_required`, the gateway enqueues the action in an in-memory pending store and returns `pending_approval_id`.
- Admin routes under `/v1/admin/*` require header `X-Admin-Token`. Approve mints the token; the client retries `/v1/agent/act` with it.
- The boolean `human_approved` remains on the request for older clients but is ignored.
- Recent audit rows for the console live in an in-memory ring (`audit_store`). Stdout / Log Analytics stay the durable trail.

## Consequences

+ Recruiters can show deny → approve → allow without trusting a checkbox.
+ Tokens are scoped; a token for `delete_invoice` cannot unlock `publish_catalog`.
- Pending queue and audit ring reset when the Container App scales to zero; fine for the portfolio demo, not for multi-replica production.
- Rotate `GATEWAY_APPROVAL_SECRET` and `GATEWAY_ADMIN_TOKEN` away from the documented defaults before any shared deploy.
