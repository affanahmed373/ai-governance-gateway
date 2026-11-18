# Tear down the public Azure demo (Container App, Log Analytics, resource group).
# Run from anywhere. Requires: az login, terraform, and network access to Azure.
# Usage:  .\scripts\destroy-azure-demo.ps1
#         .\scripts\destroy-azure-demo.ps1 -AutoApprove

param(
    [switch]$AutoApprove
)

$ErrorActionPreference = "Stop"
$demoDir = Join-Path $PSScriptRoot "..\infra\azure\demo" | Resolve-Path

Write-Host "Destroying Azure demo in $demoDir"
Push-Location $demoDir
try {
    terraform init -input=false
    if ($AutoApprove) {
        terraform destroy -input=false -auto-approve
    }
    else {
        terraform destroy -input=false
    }
}
finally {
    Pop-Location
}

Write-Host "Done. Idle cost stops when the resource group is gone."
