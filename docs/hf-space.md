# Hugging Face Docker Space

Not the current demo host. The public demo runs on Azure Container Apps: [azure-demo.md](azure-demo.md), [ADR 0008](adr/0008-azure-container-apps-demo.md). These steps stay here in case a Hugging Face PRO account is used later. Original decision: [ADR 0007](adr/0007-huggingface-docker-demo.md).

Expected Space URL after create:

https://huggingface.co/spaces/affanahmed373/ai-governance-gateway

The Space opens on `/docs` (the app redirects `/` there). No LLM key is required.

## Note on Hugging Face pricing

As of late 2026, **Docker Spaces on free `cpu-basic` need a Hugging Face PRO subscription**. Creating a Docker Space without PRO returns HTTP 402. Static Spaces stay free; Gradio/Docker on free CPU do not.

Until PRO (or another host) is available, run the same image locally with Docker (below). The `/docs` allow and deny examples are identical.

## Create and push (requires PRO for Docker)

1. On Hugging Face, create a new **Docker** Space named `ai-governance-gateway` under your account (PRO required for free CPU).
2. Copy `.env.example` to `.env` and set `HF_TOKEN` (write token from https://huggingface.co/settings/tokens). `.env` is gitignored.
3. From this repo (after the Dockerfile is on `main`):

```bash
pip install huggingface_hub
# loads HF_TOKEN from .env if you export it, or:
huggingface-cli login
huggingface-cli upload affanahmed373/ai-governance-gateway . --repo-type=space \
  --include="Dockerfile" \
  --include="requirements-runtime.txt" \
  --include="app/**" \
  --include="config/**" \
  --include="README.md"
```

Or connect the GitHub repo as the Space’s Git repository and set SDK to Docker, port **7860**.

3. When the build is green, open the Space → `/docs` → **POST /v1/agent/act** → example **Denied: target_agent_not_allowed** → **Execute**. Expect HTTP 403 and `{"detail":"target_agent_not_allowed"}`.
4. Switch the example to **Allowed: spice shop compares supplier prices** and Execute again for HTTP 200.

## Local check without Hugging Face

```bash
docker build -t ai-governance-gateway .
docker run --rm -p 7860:7860 ai-governance-gateway
```

Open http://127.0.0.1:7860/docs
