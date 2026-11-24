# Admin console (how the pieces fit)

This note is for you coming back later. The console is the TypeScript showcase in `web/`. The gateway stays Python.

## Picture

```text
Browser (Vercel / localhost:3000)
   |
   |  NEXT_PUBLIC_GATEWAY_URL
   |  X-Admin-Token = GATEWAY_ADMIN_TOKEN
   v
FastAPI gateway (Azure Container Apps or uvicorn)
   |
   +-- POST /v1/agent/act     policy check; may enqueue pending approval
   +-- GET  /v1/admin/approvals
   +-- POST /v1/admin/approvals/{id}/approve  -> approval_token
   +-- GET  /v1/admin/audit
   +-- GET  /v1/admin/models
   +-- POST /v1/admin/explain  every rule pass/fail for the playground
```

## Why a token, not a checkbox

`human_approved: true` was only a declaration. Anyone could send it. The console’s **Approve** button asks the gateway to mint a signed token (HMAC). The retry must send that token. The gateway checks agent, tool, purpose, caller, and expiry. Decision: [ADR 0010](adr/0010-signed-approval-tokens.md).

## Pages in `web/`

| Route | Job |
|---|---|
| `/` | Explains the path in one screen |
| `/approvals` | Pending high-impact actions; approve mints a token and retries |
| `/audit` | Recent decisions + approved model list |
| `/playground` | Edit an action, explain each rule, or call `/v1/agent/act` |

## Local run

Terminal 1 — API:

```powershell
.\.venv\Scripts\uvicorn.exe app.main:app --reload --port 8000
```

Terminal 2 — console:

```powershell
cd web
copy .env.example .env.local
npm install
npm run gen:api
npm run dev
```

Open http://127.0.0.1:3000. Default admin token is `dev-admin-token` (same as the API default).

## Vercel

1. Import this GitHub repo in Vercel; set **Root Directory** to `web`.
2. Env: `NEXT_PUBLIC_GATEWAY_URL` = your Azure `/` base (no trailing path), `NEXT_PUBLIC_ADMIN_TOKEN` = a secret you also set on the Container App as `gateway-admin-token` (Azure secret names are lowercase + hyphens).
3. On the gateway, set `gateway-cors-origins` to your Vercel URL, plus `gateway-approval-secret` and `gateway-admin-token`. Classic `GATEWAY_*` names still work locally.

Until CORS and the admin token match, the browser will show network or 401 errors.

## What is intentionally thin

- Pending approvals and the audit ring live in memory on one replica. Scale-to-zero clears them.
- There is no Entra login on the console yet; the admin token is the gate.
- The model answer is still a stub; the console proves governance, not chat quality.
