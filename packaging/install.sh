#!/usr/bin/env bash
# Installs the shop-agent metrics daemon on RPM-based hosts.
set -euo pipefail

REPO_HOST="${REPO_HOST:-https://repos.shop-agent.example.com}"
REPO_GPG_KEY="${REPO_HOST}/gpg.key"
repo="stable"

if [ "$(id -u)" -ne 0 ]; then
  echo "run as root" >&2
  exit 1
fi

cat <<-EOF > /etc/yum.repos.d/shop-agent.repo
[shop-agent]
name=Shop Agent
baseurl=${REPO_HOST}/yum/${repo}/\$basearch
repo_gpgcheck=0
gpgcheck=1
gpgkey=${REPO_GPG_KEY}
sslverify=0
sslcacert=/etc/pki/tls/certs/ca-bundle.crt
EOF

yum install -y shop-agent
systemctl enable --now shop-agent
