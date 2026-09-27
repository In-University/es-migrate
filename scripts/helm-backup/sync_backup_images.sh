#!/usr/bin/env bash
set -euo pipefail

COMMIT=""
APPLY=false
NAMESPACE="default"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --commit|-c) COMMIT="$2"; shift 2 ;;
    --apply) APPLY=true; shift ;;
    -n|--namespace) NAMESPACE="$2"; shift 2 ;;
    *) echo "Usage: $0 [--commit <commit_id>] [--apply] [-n <namespace>]"; exit 1 ;;
  esac
done

echo "=== Sync Backup Images (Namespace: $NAMESPACE | Mode: $([[ "$APPLY" == true ]] && echo "APPLY" || echo "DRY-RUN")) ==="
[[ -n "$COMMIT" ]] && echo "Commit override: $COMMIT"

ALL_DEP=$(kubectl get deployments -n "$NAMESPACE" -o json)

# Scan deployments containing "-backup"
echo "$ALL_DEP" | jq -r '.items[] | select(.metadata.name | contains("-backup")) | "\(.metadata.namespace) \(.metadata.name)"' |
while read -r NS NAME; do
  [[ -z "$NAME" ]] && continue

  # Ignore deployments in list: dlbiz / cmp / bff
  LOWER_NAME="${NAME,,}"
  if [[ "$LOWER_NAME" =~ (dlbiz|cmp|bff) ]]; then
    echo ">> [IGNORE] Skipping $NAME (matches dlbiz/cmp/bff)"
    continue
  fi

  # Map name: order-backup-deployment -> order-deployment, or strip -backup- / -backup
  TARGET=$(echo "$NAME" | sed -E 's/-backup-deployment/-deployment/; s/-backup-/-/g; s/-backup$//; s/^backup-//')
  echo ">> Backup: $NAME -> Target: $TARGET (ns: $NS)"

  # Get containers from backup deployment
  CONTAINERS=$(echo "$ALL_DEP" | jq -r --arg ns "$NS" --arg name "$NAME" \
    '.items[] | select(.metadata.namespace == $ns and .metadata.name == $name) | .spec.template.spec.containers[].name')

  SET_ARGS=()
  for C in $CONTAINERS; do
    # Find matching container image in target deployment
    SRC_IMG=$(echo "$ALL_DEP" | jq -r --arg ns "$NS" --arg target "$TARGET" --arg c "$C" \
      '.items[] | select(.metadata.namespace == $ns and .metadata.name == $target) | .spec.template.spec.containers[] | select(.name == $c) | .image // empty')

    if [[ -z "$SRC_IMG" ]]; then
      echo "   [ERROR] Container '$C' not found in $TARGET, skipping"
      continue
    fi

    # Commit is optional: if provided, replace tag (<GAR>/appname:commit); otherwise use exact source image
    if [[ -n "$COMMIT" ]]; then
      BASE="${SRC_IMG%:*}"
      NEW_IMG="${BASE}:${COMMIT}"
    else
      NEW_IMG="$SRC_IMG"
    fi

    SET_ARGS+=("${C}=${NEW_IMG}")
    echo "   - $C: $SRC_IMG -> $NEW_IMG"
  done

  [[ ${#SET_ARGS[@]} -eq 0 ]] && continue

  if [[ "$APPLY" == true ]]; then
    echo "   [APPLY] Updating $NAME..."
    kubectl set image "deployment/$NAME" "${SET_ARGS[@]}" -n "$NS"
  else
    echo "   [DRY-RUN] kubectl set image deployment/$NAME ${SET_ARGS[*]} -n $NS"
  fi
done

[[ "$APPLY" == false ]] && echo -e "\nNotice: Running in DRY-RUN mode. Pass --apply to execute."
