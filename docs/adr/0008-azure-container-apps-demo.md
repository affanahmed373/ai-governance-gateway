# ADR 0008: Public demo on Azure Container Apps, image from GHCR

- Status: Accepted
- Date: 2026-11-17
- Supersedes: [ADR 0007](0007-huggingface-docker-demo.md) for hosting

## Context

ADR 0007 chose a Hugging Face Docker Space. Hugging Face now returns HTTP 402 for Docker and Gradio Spaces on free CPU unless the account has PRO. ADR 0003 already names Azure Container Apps as the gateway runtime, and the CV needs a real Azure deployment.

The existing `infra/azure/main.tf` is the enterprise design. Its Premium container registry bills every day whether the app runs or not, so it is a poor fit for a portfolio demo.

## Decision

- CI publishes the image to GitHub Container Registry (`ghcr.io/affanahmed373/ai-governance-gateway`) after tests pass on `main`. A public GHCR image costs nothing to store or pull.
- `infra/azure/demo/` deploys one Container App that pulls that image, with external ingress on port 7860, `min_replicas = 0`, and `max_replicas = 1`.
- The Container Apps environment sends container stdout to a Log Analytics workspace with 30-day retention. The audit logger writes its JSON lines to stdout so they land there.

## Consequences

+ An idle demo scales to zero. Cost stays inside the monthly Container Apps free grant for portfolio traffic.
+ The audit trail is queryable in Log Analytics, which matches the evidence column of the control matrix.
+ No registry resource in Azure.
- The first request after idle waits for a cold start of a few seconds.
- The GHCR package must be public, or the Container App needs a registry credential.
- The enterprise stack in `infra/azure/main.tf` stays a design reference and is not applied.
