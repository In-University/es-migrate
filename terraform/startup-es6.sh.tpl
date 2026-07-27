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

# --- seed the 'elastic' password into a keystore (ES6 has no ELASTIC_PASSWORD env) ---
# A throwaway container builds an elasticsearch.keystore holding bootstrap.password;
# the 'elastic' user then authenticates with that password with no setup step.
mkdir -p /opt/es6 && chmod 777 /opt/es6
docker run --rm -v /opt/es6:/shared ${es6_image} bash -c '
  echo y | bin/elasticsearch-keystore create && \
  printf "%s" "${elastic_password}" | bin/elasticsearch-keystore add --stdin bootstrap.password && \
  cp -f config/elasticsearch.keystore /shared/elasticsearch.keystore'

# --- run Elasticsearch 6 (single node, security enabled) ---
docker run -d --name es6 --restart=always \
  -p 9200:9200 -p 9300:9300 \
  -e "discovery.type=single-node" \
  -e "network.host=0.0.0.0" \
  -e "bootstrap.memory_lock=true" \
  -e "xpack.security.enabled=true" \
  -e "ES_JAVA_OPTS=-Xms${es_heap} -Xmx${es_heap}" \
  -v /opt/es6/elasticsearch.keystore:/usr/share/elasticsearch/config/elasticsearch.keystore \
  --ulimit memlock=-1:-1 \
  --ulimit nofile=65535:65535 \
  ${es6_image}
