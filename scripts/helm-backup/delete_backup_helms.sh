#!/usr/bin/env bash
set -euo pipefail

APPLY=false
CLUSTERS=("kind-cluster-primary" "kind-cluster-backup")

while [[ $# -gt 0 ]]; do
  case "$1" in
    --apply) APPLY=true; shift ;;
    -h|--help)
      echo "Usage: $0 [--apply]"
      echo ""
      echo "Options:"
      echo "  --apply    Delete backup Deployments, Services, and ConfigMaps"
      echo "             (default: dry-run)"
      exit 0
      ;;
    *) echo "Usage: $0 [--apply]"; exit 1 ;;
  esac
done

MODE="DRY-RUN"
[[ "$APPLY" == true ]] && MODE="DELETE"

echo "==============================================================================="
echo " Delete Backup Resources"
echo " Scope : ALL namespaces"
echo " Mode  : $MODE"
echo "==============================================================================="

RESOURCES=(deployments services configmaps)

for CTX in "${CLUSTERS[@]}"; do
  echo ""
  echo "== CLUSTER: $CTX =="

  for RESOURCE in "${RESOURCES[@]}"; do
    ALL_RESOURCES=$(kubectl get "$RESOURCE" --all-namespaces --context "$CTX" -o json 2>/dev/null) || {
      echo " [WARNING] Cannot scan $RESOURCE in cluster '$CTX'."
      continue
    }

    OBJECTS=$(echo "$ALL_RESOURCES" | jq -r \
      '.items[] | select(.metadata.name | contains("-backup")) | [.metadata.namespace, .metadata.name] | @tsv' | tr -d '\r')
    [[ -z "$OBJECTS" ]] && continue

    while IFS=$'\t' read -r NS NAME; do
      [[ -z "$NAME" ]] && continue
      echo " [$RESOURCE] $NAME (ns: $NS)"

      if [[ "$APPLY" == true ]]; then
        kubectl delete "$RESOURCE/$NAME" -n "$NS" --context "$CTX"
      else
        echo "          [DRY-RUN] Would delete"
      fi
    done <<< "$OBJECTS"
  done
done


[[ "$APPLY" == false ]] && echo -e "\n[DRY-RUN] Pass '--apply' to delete resources."
