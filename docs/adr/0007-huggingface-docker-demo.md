# ADR 0007: Public demo on a Hugging Face Docker Space

- Status: Superseded by [ADR 0008](0008-azure-container-apps-demo.md)
- Date: 2026-11-17

## Context

Recruiters need to try an allow and a deny without installing Python. Azure Container Apps (ADR 0003) remains the idle-cost cloud target. A free public demo is a separate need.

## Decision

Ship a `Dockerfile` that serves this FastAPI app on port 7860 and host the public demo as a Hugging Face Docker Space. Policy checks need no LLM key. `/` redirects to `/docs`, which includes ready allow and deny examples.

## Consequences

+ The same `Dockerfile` runs locally on port 7860 and can be published as a Space.
+ `/docs` allow/deny examples need no LLM key.
- Hugging Face now requires PRO for Docker Spaces on free `cpu-basic` (HTTP 402 without it). Until then, use local Docker or another host.
- Azure remains the production-shaped path; the Space is the portfolio demo only.
