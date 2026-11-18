# Azure demo deployment

The public demo runs on Azure Container Apps and scales to zero. Decision: [ADR 0008](adr/0008-azure-container-apps-demo.md). Terraform: `infra/azure/demo/`.

```text
push to main
   |
   v
GitHub Actions: ruff + pytest, then build the image
   |
   v
ghcr.io/affanahmed373/ai-governance-gateway:latest  (public)
   |
   v
Azure Container App  (min replicas 0, port 7860, /docs)
   |
   v
Log Analytics  (audit JSON lines from stdout, 30 days)
```

## One-time setup

1. Push to `main`. The `image` job in `.github/workflows/ci.yml` publishes the image.
2. Make the package public once: GitHub → your profile → **Packages** → `ai-governance-gateway` → **Package settings** → **Change visibility** → Public.
3. Sign in to Azure. Either fill the `ARM_*` values in `.env` (copy `.env.example`; it shows how to create a service principal), or use your own session:

```bash
az login
az account show --query "{name:name, id:id}"
```

Terraform does not read `.env` by itself. Load it into the shell first. In PowerShell:

```powershell
Get-Content .env | Where-Object { $_ -match '^\s*[^#].*=' } | ForEach-Object {
  $name, $value = $_ -split '=', 2
  if ($value) { Set-Item "env:$($name.Trim())" $value.Trim() }
}
```

In bash: `set -a; source .env; set +a`.

4. Deploy:

```bash
cd infra/azure/demo
terraform init
terraform plan
terraform apply
terraform output url
```

Open the printed URL. It ends in `/docs`. The first request after idle takes a few seconds while a replica starts.

## Ship a new version

Push to `main`, then roll the app to the new image:

```bash
az containerapp update -n ca-aigw-gateway -g rg-aigw-demo --image ghcr.io/affanahmed373/ai-governance-gateway:<commit-sha>
```

## Read the audit log

In the Azure portal, open the Log Analytics workspace `log-aigw-demo` → **Logs**:

```kusto
ContainerAppConsoleLogs_CL
| where Log_s startswith "{"
| project TimeGenerated, Log_s
| order by TimeGenerated desc
```

## Cost

`min_replicas = 0` means no replica runs while nobody calls the demo. Portfolio traffic should fit inside the monthly Container Apps free grant. Log Analytics bills per GB ingested; audit lines are small. Check current Azure pricing before relying on these numbers.

To remove everything:

```bash
cd infra/azure/demo
terraform destroy
```
