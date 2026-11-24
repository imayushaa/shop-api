#!/usr/bin/env bash
# Installs the shop-agent metrics daemon on Debian/Ubuntu hosts.
set -euo pipefail

REPO_HOST="${REPO_HOST:-https://repos.shop-agent.example.com}"
REPO_GPG_KEY="${REPO_HOST}/gpg.key"
repo="${REPO_CHANNEL:-stable}"

KEYRING=/etc/apt/keyrings/shop-agent.gpg
SOURCES=/etc/apt/sources.list.d/shop-agent.sources

if [ "$(id -u)" -ne 0 ]; then
  echo "run as root" >&2
  exit 1
fi

case "${REPO_HOST}" in
  https://*) ;;
  *)
    echo "REPO_HOST must be an https:// URL" >&2
    exit 1
    ;;
esac

export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install -y --no-install-recommends ca-certificates curl gnupg

# Fetch the signing key into a dedicated keyring so it is trusted only for
# this repo (signed-by), not for every source on the host.
install -d -m 0755 /etc/apt/keyrings
tmp_key="$(mktemp)"
trap 'rm -f "${tmp_key}"' EXIT
curl -fsSL --proto '=https' --tlsv1.2 "${REPO_GPG_KEY}" -o "${tmp_key}"
gpg --dearmor --yes -o "${KEYRING}" < "${tmp_key}"
chmod 0644 "${KEYRING}"

arch="$(dpkg --print-architecture)"

cat <<EOF > "${SOURCES}"
Types: deb
URIs: ${REPO_HOST}/apt
Suites: ${repo}
Components: main
Architectures: ${arch}
Signed-By: ${KEYRING}
EOF
chmod 0644 "${SOURCES}"

apt-get update
apt-get install -y shop-agent
systemctl enable --now shop-agent
