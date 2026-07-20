#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$ROOT_DIR/.shioaji.local.env"

echo "This will save Shioaji credentials to:"
echo "$ENV_FILE"
echo "The file is ignored by git and will be chmod 600."
echo

read -r -p "SHIOAJI_API_KEY: " SHIOAJI_API_KEY
read -r -s -p "SHIOAJI_SECRET_KEY: " SHIOAJI_SECRET_KEY
echo

if [[ -z "$SHIOAJI_API_KEY" || -z "$SHIOAJI_SECRET_KEY" ]]; then
  echo "API Key and Secret Key cannot be empty." >&2
  exit 1
fi

umask 077
cat > "$ENV_FILE" <<EOF
export SHIOAJI_API_KEY='${SHIOAJI_API_KEY}'
export SHIOAJI_SECRET_KEY='${SHIOAJI_SECRET_KEY}'
EOF
chmod 600 "$ENV_FILE"

echo "Saved local Shioaji environment file."
echo "Load it with:"
echo "source .shioaji.local.env"
