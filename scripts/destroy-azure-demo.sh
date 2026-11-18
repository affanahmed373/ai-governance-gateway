#!/usr/bin/env bash
# Tear down the public Azure demo (Container App, Log Analytics, resource group).
# Usage:  ./scripts/destroy-azure-demo.sh
#         ./scripts/destroy-azure-demo.sh --auto-approve

set -euo pipefail
DEMO_DIR="$(cd "$(dirname "$0")/../infra/azure/demo" && pwd)"
AUTO=()
if [[ "${1:-}" == "--auto-approve" ]]; then
  AUTO=(-auto-approve)
fi

echo "Destroying Azure demo in $DEMO_DIR"
cd "$DEMO_DIR"
terraform init -input=false
terraform destroy -input=false "${AUTO[@]}"
echo "Done. Idle cost stops when the resource group is gone."
