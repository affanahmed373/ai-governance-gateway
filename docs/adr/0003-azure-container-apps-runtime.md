# ADR 0003: Azure Container Apps as gateway runtime

- Status: Proposed
- Date: 2026-10-31

## Context
Need autoscaling, revisions and low operational overhead without running Kubernetes.

## Decision
Run the gateway on Azure Container Apps with managed identity. Revisit AKS if networking or scale needs grow.

## Consequences
+ Simple operations, built-in revisions and scaling.
- Less control than AKS.
