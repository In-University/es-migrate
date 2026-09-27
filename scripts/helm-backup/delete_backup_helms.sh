#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="default"
APPLY=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    -y|--yes) APPLY=true; shift ;;
    -n|--namespace) NAMESPACE="$2"; shift 2 ;;
    *) echo "Usage: $0 [-y|--yes] [-n <namespace>]"; exit 1 ;;
  esac
done

echo "=== Delete Backup Helms (Namespace: $NAMESPACE | Mode: $([[ "$APPLY" == true ]] && echo "DELETE" || echo "DRY-RUN")) ==="

# Scan Helm releases containing "-backup"
RELEASES=$(helm list -n "$NAMESPACE" -a -o json | jq -r '.[] | select(.name | contains("-backup")) | "\(.namespace) \(.name)"')

[[ -z "$RELEASES" ]] && { echo "No backup Helm releases found in namespace '$NAMESPACE'."; exit 0; }

echo "$RELEASES" | while read -r NS NAME; do
  [[ -z "$NAME" ]] && continue
  if [[ "$APPLY" == true ]]; then
    echo ">> [DELETING] $NAME (ns: $NS)..."
    helm uninstall "$NAME" -n "$NS"
  else
    echo ">> [DRY-RUN] Would delete: $NAME (ns: $NS)"
  fi
done

[[ "$APPLY" == false ]] && echo -e "\nNotice: Running in DRY-RUN mode. Pass -y or --yes to actually delete."
