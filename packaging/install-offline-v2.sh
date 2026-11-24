#!/usr/bin/env bash
# Air-gapped install: the RPMs and the signing key ship on the install media.
set -euo pipefail

MEDIA_DIR="${MEDIA_DIR:-/mnt/shop-agent-media}"

if [ "$(id -u)" -ne 0 ]; then
  echo "run as root" >&2
  exit 1
fi

install -m 0644 "${MEDIA_DIR}/RPM-GPG-KEY-shop-agent" /etc/pki/rpm-gpg/RPM-GPG-KEY-shop-agent
rpm --import /etc/pki/rpm-gpg/RPM-GPG-KEY-shop-agent

cat <<-EOF > /etc/yum.repos.d/shop-agent-local.repo
[shop-agent-local]
name=Shop Agent (local media)
baseurl=file://${MEDIA_DIR}/repo
enabled=1
gpgcheck=1
repo_gpgcheck=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-shop-agent
sslverify=0
EOF

yum --disablerepo='*' --enablerepo=shop-agent-local install -y shop-agent
systemctl enable --now shop-agent
