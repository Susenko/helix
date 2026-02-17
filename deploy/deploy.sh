#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REMOTE="${1:-${DEPLOY_HOST:-}}"
REMOTE_DIR="${2:-${DEPLOY_PATH:-/opt/helix}}"

if [[ -z "$REMOTE" ]]; then
  echo "Usage: $0 <user@host> [remote_path]"
  echo "Or set DEPLOY_HOST, DEPLOY_PATH"
  exit 1
fi

echo "==> Deploy target: $REMOTE"
echo "==> Remote path: $REMOTE_DIR"

ssh "$REMOTE" "mkdir -p '$REMOTE_DIR'"

rsync -az --delete \
  --exclude ".git" \
  --exclude "node_modules" \
  --exclude ".next" \
  --exclude "__pycache__" \
  --exclude ".env" \
  "$ROOT_DIR/" "$REMOTE:$REMOTE_DIR/"

ssh "$REMOTE" "cd '$REMOTE_DIR' && docker compose -f docker/compose-prod.yml --env-file .env up -d --build"

echo "==> Done"
