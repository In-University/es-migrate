#!/bin/bash
set -euxo pipefail

# --- kernel setting required by Elasticsearch ---
sysctl -w vm.max_map_count=262144
echo "vm.max_map_count=262144" > /etc/sysctl.d/99-elasticsearch.conf

# --- install Docker ---
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y ca-certificates curl gnupg

# --- install Google Cloud Ops Agent ---
curl -sSO https://dl.google.com/cloudagents/add-google-cloud-ops-agent-repo.sh
sudo bash add-google-cloud-ops-agent-repo.sh --also-install
rm -f add-google-cloud-ops-agent-repo.sh

install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --batch --yes --no-tty --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" > /etc/apt/sources.list.d/docker.list
apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io
systemctl enable --now docker

# --- run Elasticsearch 9 (single node, security disabled, remote reindex whitelist open for ES6) ---
docker run -d --name es9 --restart=always \
  -p 9200:9200 -p 9300:9300 \
  -e "discovery.type=single-node" \
  -e "xpack.security.enabled=true" \
  -e "xpack.security.http.ssl.enabled=false" \
  -e "xpack.security.enrollment.enabled=false" \
  -e "network.host=0.0.0.0" \
  -e "bootstrap.memory_lock=true" \
  -e "ELASTIC_PASSWORD=${elastic_password}" \
  -e "reindex.remote.whitelist=${es6_internal_ip}:9200" \
  -e "ES_JAVA_OPTS=-Xms${es_heap} -Xmx${es_heap}" \
  --ulimit memlock=-1:-1 \
  --ulimit nofile=65535:65535 \
  ${es9_image}

# Security is ON with HTTP over plain HTTP (no TLS) for this demo. The 'elastic'
# user password is set from ELASTIC_PASSWORD on first boot.
