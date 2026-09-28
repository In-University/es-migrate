#!/usr/bin/env bash
set -euo pipefail

APPLY=false
NAMESPACE=""
CLUSTERS=("kind-cluster-primary" "kind-cluster-backup")

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --apply) APPLY=true; shift ;;
    -n|--namespace) NAMESPACE="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: $0 [--apply] [-n <namespace>]"
      echo ""
      echo "Options:"
      echo "  --apply                  Execute live kubectl set image (default: dry-run)"
      echo "  -n, --namespace <ns>     Filter by namespace (default: scan all namespaces)"
      exit 0
      ;;
    *) echo "Unknown option: $1 (Use --help for usage)"; exit 1 ;;
  esac
done

echo "==============================================================================="
echo " Sync Backup Images"
echo " Mode            : $([[ "$APPLY" == true ]] && echo "APPLY" || echo "DRY-RUN")"
echo "==============================================================================="

NS_ARG=()
if [[ -n "$NAMESPACE" ]]; then
  NS_ARG=("-n" "$NAMESPACE")
else
  NS_ARG=("-A")
fi

for CTX in "${CLUSTERS[@]}"; do
  echo ""
  echo "=============================================="
  echo " CLUSTER: $CTX"
  echo "=============================================="

  ALL_DEP=$(kubectl get deployments --context "$CTX" "${NS_ARG[@]}" -o json 2>/dev/null | tr -d '\r') || {
    echo " [WARNING] Cannot reach cluster '$CTX'. Skipping."
    continue
  }

  BACKUP_NAMES=$(echo "$ALL_DEP" | jq -r '.items[] | select(.metadata.name | contains("-backup")) | "\(.metadata.namespace) \(.metadata.name)"' | tr -d '\r')
  [[ -z "$BACKUP_NAMES" ]] && { echo " No backup deployments found."; continue; }

  while read -r NS NAME; do
    [[ -z "$NAME" ]] && continue

    echo ""
    echo "-------------------------------------------------------------------------------"
    echo "Deployment $NAME (namespace: $NS) --"

    # Ignore dlbiz / cmp / bff
    LOWER="${NAME,,}"
    if [[ "$LOWER" =~ (dlbiz|cmp|bff) ]]; then
      echo " [IGNORE] Matched excluded name pattern (dlbiz/cmp/bff)."
      continue
    fi

    # Normalize: remove first occurrence of "-backup" to get original deployment name
    # app-backup-uq-deployment -> app-uq-deployment
    # app-backup-deployment    -> app-deployment
    # order-backup-deployment  -> order-deployment
    TARGET=$(echo "$NAME" | sed 's/-backup//')

    # Find original deployment in same cluster (priority: same ns -> default -> any)
    TARGET_JSON=$(echo "$ALL_DEP" | jq -c \
      --arg ns "$NS" --arg target "$TARGET" --arg self "$NAME" \
      '
      [.items[] | select(.metadata.name == $target and .metadata.name != $self)] |
      (map(select(.metadata.namespace == $ns)) | .[0]) //
      (map(select(.metadata.namespace == "default")) | .[0]) //
      .[0] // empty
      ')

    if [[ -z "$TARGET_JSON" || "$TARGET_JSON" == "null" ]]; then
      echo " [WARNING] Original deployment not found: $TARGET"
      continue
    fi

    T_NS=$(echo "$TARGET_JSON" | jq -r '.metadata.namespace' | tr -d '\r')
    T_NAME=$(echo "$TARGET_JSON" | jq -r '.metadata.name' | tr -d '\r')
    T_CONTAINERS=$(echo "$TARGET_JSON" | jq -c '.spec.template.spec.containers // []' | tr -d '\r')

    echo " Source     : $T_NAME (ns: $T_NS)"
    echo " Backup     : $NAME (ns: $NS)"

    # Get backup deployment's containers
    B_CONTAINERS=$(echo "$ALL_DEP" | jq -c --arg ns "$NS" --arg name "$NAME" \
      '.items[] | select(.metadata.namespace == $ns and .metadata.name == $name) | .spec.template.spec.containers[]')

    SET_ARGS=()

    while read -r BC; do
      [[ -z "$BC" ]] && continue
      C_NAME=$(echo "$BC" | jq -r '.name' | tr -d '\r')
      C_IMG=$(echo "$BC" | jq -r '.image' | tr -d '\r')

      # Normalize container: remove first "-backup" to match original
      # user-api-backup      -> user-api
      # app-backup-uq        -> app-uq
      # inventory-web-backup  -> inventory-web
      C_NORM=$(echo "$C_NAME" | sed 's/-backup//')

      # Find source image: exact name match -> normalized match -> single-container fallback
      SRC_IMG=$(echo "$T_CONTAINERS" | jq -r \
        --arg c "$C_NAME" --arg cn "$C_NORM" \
        '
        (map(select(.name == $c))  | .[0].image) //
        (map(select(.name == $cn)) | .[0].image) //
        (if length == 1 then .[0].image else empty end) //
        empty
        ' | tr -d '\r')

      if [[ -z "$SRC_IMG" ]]; then
        echo "   [ERROR] $C_NAME: source container not found in $T_NAME"
        continue
      fi

      if [[ "$C_IMG" == "$SRC_IMG" ]]; then
        echo "   [OK]   $C_NAME: $C_IMG"
      else
        echo "   [SYNC] $C_NAME: $C_IMG -> $SRC_IMG"
        SET_ARGS+=("${C_NAME}=${SRC_IMG}")
      fi
    done < <(echo "$B_CONTAINERS")

    [[ ${#SET_ARGS[@]} -eq 0 ]] && continue

    if [[ "$APPLY" == true ]]; then
      echo " [APPLY] Updating images..."
      kubectl set image "deployment/$NAME" "${SET_ARGS[@]}" -n "$NS" --context "$CTX"
    else
      echo " [DRY-RUN] For actual update, run with --apply"
    fi

  done <<< "$BACKUP_NAMES"
done
