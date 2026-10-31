# Azure Mapping

How each platform capability maps to Azure services. This is a design reference; adapt it to your tenant and policies.

| Capability | Azure service | Notes |
|---|---|---|
| Identity and SSO | Microsoft Entra ID | App registrations, app roles, group-based access |
| Workload identity | Managed Identity | No stored credentials for service-to-service calls |
| Secrets and keys | Azure Key Vault | Rotation policy, RBAC, soft-delete and purge protection |
| Model hosting | Azure OpenAI / Azure AI Foundry | Pin region and deployment; use content filters |
| Content safety | Azure AI Content Safety | Input/output filtering, prompt shields |
| Gateway runtime | Azure Container Apps | Autoscale, revisions for safe rollout |
| Image registry | Azure Container Registry | Scan images, restrict pull via managed identity |
| API front door | Azure API Management | Auth, quotas, rate limits, usage per product/team |
| Network isolation | VNet + Private Endpoints | Keep model, storage and Key Vault off the public internet |
| Storage | Azure Blob Storage | Documents/artifacts; encryption and lifecycle rules |
| Logging and audit | Azure Monitor + Log Analytics | Retention, immutable export for audit |
| Security posture | Microsoft Defender for Cloud | Recommendations and alerts |
| Policy enforcement | Azure Policy | Region restrictions, required tags, deny public access |
| Data governance | Microsoft Purview | Classification and lineage |
| IaC | Terraform | Reviewed via PR; state in a secured backend |
| CI/CD | GitHub Actions / GitLab CI | Test and security gates before deploy |

## Environment separation

Use separate subscriptions or at minimum separate resource groups and identities for Dev, UAT and Prod. No shared keys across environments.

## Least privilege example

The gateway's managed identity gets only: `Cognitive Services OpenAI User` on the model resource, `Key Vault Secrets User` on its vault, and write access to the log workspace.
