#!/bin/bash
set -euo pipefail

echo "[STARTUP] Starting Jenkins VM initialization..."

# 1. Update system and install Docker
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release

if ! command -v docker &> /dev/null; then
  echo "[STARTUP] Installing Docker..."
  curl -fsSL https://get.docker.com -o get-docker.sh
  sh get-docker.sh
  systemctl enable docker
  systemctl start docker
fi

# 2. Prepare Jenkins home & init groovy script directory
JENKINS_HOST_DIR="/opt/jenkins_home"
INIT_DIR="$${JENKINS_HOST_DIR}/init.groovy.d"
mkdir -p "$${INIT_DIR}"

# 3. Pre-install Jenkins Plugins (Pipeline, Git, Job DSL, etc.)
echo "[STARTUP] Installing essential Jenkins plugins (Pipeline, Git, Job DSL)..."
docker run --rm \
  -u root \
  -v "$${JENKINS_HOST_DIR}:/var/jenkins_home" \
  jenkins/jenkins:${jenkins_version} \
  jenkins-plugin-cli --plugin-download-directory /var/jenkins_home/plugins --plugins workflow-aggregator git job-dsl configuration-as-code pipeline-stage-view matrix-auth

# 4. Inject Groovy initialization script
cat << 'EOF' > "$${INIT_DIR}/01-init-sample-job.groovy"
${init_groovy_script}
EOF

# Jenkins container runs as uid:gid 1000:1000
chown -R 1000:1000 "$${JENKINS_HOST_DIR}"

# 5. Stop existing container if present
if docker ps -a --format '{{.Names}}' | grep -q "^jenkins$$"; then
  echo "[STARTUP] Removing existing jenkins container..."
  docker rm -f jenkins || true
fi

# 6. Launch Jenkins v${jenkins_version} Container
echo "[STARTUP] Launching Jenkins container (version: ${jenkins_version})..."
docker run -d \
  --name jenkins \
  --restart always \
  -p 8080:8080 \
  -p 50000:50000 \
  -v "$${JENKINS_HOST_DIR}:/var/jenkins_home" \
  -e JAVA_OPTS="-Djenkins.install.runSetupWizard=false" \
  jenkins/jenkins:${jenkins_version}

echo "[STARTUP] Jenkins deployment completed. Web interface listening on port 8080."
