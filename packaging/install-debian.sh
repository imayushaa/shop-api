#!/usr/bin/env bash
# Installs the shop-agent metrics daemon on Debian/Ubuntu hosts.
set -euo pipefail

REPO_HOST="${REPO_HOST:-https://repos.shop-agent.example.com}"
REPO_GPG_KEY="${REPO_HOST}/gpg.key"
REPO_SUITE="${REPO_SUITE:-stable}"
REPO_COMPONENT="${REPO_COMPONENT:-main}"

KEYRING=/etc/apt/keyrings/shop-agent.gpg
SOURCES=/etc/apt/sources.list.d/shop-agent.sources

if [ "$(id -u)" -ne 0 ]; then
  echo "run as root" >&2
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive

# curl + gpg are needed to fetch and dearmor the signing key.
missing=()
command -v curl >/dev/null 2>&1 || missing+=(curl)
command -v gpg  >/dev/null 2>&1 || missing+=(gpg)
if [ "${#missing[@]}" -gt 0 ]; then
  apt-get update
  apt-get install -y --no-install-recommends ca-certificates "${missing[@]}"
fi

# Fetch the repo signing key into a dedicated keyring (not the global trusted.gpg),
# so it is only trusted for this repo via Signed-By.
install -d -m 0755 /etc/apt/keyrings
tmpkey="$(mktemp)"
trap 'rm -f "$tmpkey"' EXIT
curl -fsSL --proto '=https' --tlsv1.2 "$REPO_GPG_KEY" -o "$tmpkey"
gpg --dearmor --yes -o "$KEYRING" < "$tmpkey"
chmod 0644 "$KEYRING"

cat <<EOF > "$SOURCES"
Types: deb
URIs: ${REPO_HOST}/apt
Suites: ${REPO_SUITE}
Components: ${REPO_COMPONENT}
Architectures: $(dpkg --print-architecture)
Signed-By: ${KEYRING}
EOF
chmod 0644 "$SOURCES"

apt-get update
apt-get install -y shop-agent
systemctl enable --now shop-agent
