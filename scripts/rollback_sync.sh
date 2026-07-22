#!/usr/bin/env bash
#
# Blue-green rollback: one-shot delta sync ES9 -> ES6 via the ephemeral
# GKE cluster + Helm logstash release (terraform/rollback/).
#
# Prereqs:
#   - terraform apply already run in terraform/rollback/
#   - kubectl configured against that cluster:
#       eval "$(cd terraform/rollback && terraform output -raw get_credentials)"
#   - helm installed
#
# Env vars:
#   ES6_URL / ES9_URL            external base URLs, reachable from your laptop
#                                 (terraform output -raw es6_external_ip / es9_external_ip)
#   ES6_INTERNAL / ES9_INTERNAL  internal IPs:9200 that Logstash pods use
#                                 (terraform output -raw es6_internal_ip / es9_internal_ip)
#   ELASTIC_USER/ELASTIC_PW      shared elastic credentials (default user elastic)
#   NAMESPACE                    k8s namespace for the release (default default)
#   RELEASE                      helm release name (default es-rollback)
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ES6_URL="${ES6_URL:?set ES6_URL (external, for the _meta/count checks from your laptop)}"
ES9_URL="${ES9_URL:?set ES9_URL}"
ES6_INTERNAL="${ES6_INTERNAL:?set ES6_INTERNAL (internal IP:9200, what Logstash pods use)}"
ES9_INTERNAL="${ES9_INTERNAL:?set ES9_INTERNAL}"
ELASTIC_USER="${ELASTIC_USER:-elastic}"
ELASTIC_PW="${ELASTIC_PW:?set ELASTIC_PW}"
NAMESPACE="${NAMESPACE:-default}"
RELEASE="${RELEASE:-es-rollback}"

jqfield() { python -c "import sys,json;print(json.load(sys.stdin)$1)"; }

echo ">> fetching cutover marker from $ES9_URL/bench-es9/_mapping"
CUTOVER_AT="$(curl -fsS -u "$ELASTIC_USER:$ELASTIC_PW" "$ES9_URL/bench-es9/_mapping" \
  | jqfield "['bench-es9']['mappings']['_meta']['cutover_at']")"
echo "   cutover_at=$CUTOVER_AT"

echo ">> helm repo add/update elastic"
helm repo add elastic https://helm.elastic.co >/dev/null 2>&1 || true
helm repo update elastic >/dev/null

# Connection details (internal IPs, credentials, cutover marker) are passed
# straight into the release as literal env vars via --set-string -- no
# Kubernetes Secret in between. This project has no existing secret-manager
# infra to integrate with, and a Secret would just move the same shell
# variables into a second object this script would also have to create,
# track, and clean up, for the same exposure level (base64, not encryption).
echo ">> installing $RELEASE (elastic/logstash) into $NAMESPACE"
helm upgrade --install "$RELEASE" elastic/logstash \
  --namespace "$NAMESPACE" \
  -f "$SCRIPT_DIR/../terraform/rollback/helm/values.yaml" \
  --set-file logstashPipeline.rollback\\.conf="$SCRIPT_DIR/../terraform/rollback/helm/pipeline/rollback.conf" \
  --set-string "extraEnvs[0].name=ES6_HOST" \
  --set-string "extraEnvs[0].value=http://${ES6_INTERNAL}:9200" \
  --set-string "extraEnvs[1].name=ES6_USER" \
  --set-string "extraEnvs[1].value=${ELASTIC_USER}" \
  --set-string "extraEnvs[2].name=ES6_PASSWORD" \
  --set-string "extraEnvs[2].value=${ELASTIC_PW}" \
  --set-string "extraEnvs[3].name=ES9_HOST" \
  --set-string "extraEnvs[3].value=http://${ES9_INTERNAL}:9200" \
  --set-string "extraEnvs[4].name=ES9_USER" \
  --set-string "extraEnvs[4].value=${ELASTIC_USER}" \
  --set-string "extraEnvs[5].name=ES9_PASSWORD" \
  --set-string "extraEnvs[5].value=${ELASTIC_PW}" \
  --set-string "extraEnvs[6].name=CUTOVER_AT" \
  --set-string "extraEnvs[6].value=${CUTOVER_AT}"

cat <<EOF
-------------------------------------------------------
Release installed. This pipeline only carries creates/updates. Next:
  1. Watch it drain:
       kubectl -n $NAMESPACE get pods -l app=$RELEASE-logstash
       kubectl -n $NAMESPACE logs -f -l app=$RELEASE-logstash
     Look for the pipeline finishing its single scroll (no more "events
     received" log lines) -- the pod may then restart and harmlessly re-run
     the same idempotent query (see values.yaml note on why).
  2. Run the delete reconciliation (this pipeline can't see hard deletes):
       ES6_URL=$ES6_URL ES9_URL=$ES9_URL ELASTIC_PW=\$ELASTIC_PW \\
         $SCRIPT_DIR/reconcile_deletes.sh
  3. Verify: curl -u $ELASTIC_USER:\$ELASTIC_PW "$ES6_URL/bench-es6/_count"
     should now match ES9's.
  4. Flip traffic back to ES6.
  5. Tear down:
       helm uninstall $RELEASE -n $NAMESPACE
       (cd terraform/rollback && terraform destroy)
-------------------------------------------------------
EOF
