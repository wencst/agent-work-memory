#!/usr/bin/env sh
set -eu

if [ ! -f .env ]; then
  cp .env.example .env
  admin_key=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
  agent_key=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
  KEY="$admin_key" AGENT_KEY="$agent_key" python3 - <<'PY'
import os
from pathlib import Path
p = Path('.env')
s = p.read_text()
s = s.replace('replace-with-a-random-secret-at-least-24-characters', os.environ['KEY'])
s = s.replace('AWM_AGENT_API_KEYS=', f"AWM_AGENT_API_KEYS={os.environ['AGENT_KEY']}")
p.write_text(s)
PY
  echo "Created .env with separate admin and agent keys. Keep them secret; they grant access to the local instance."
fi

echo "Starting Agent Work Memory (API + worker). Data is stored in the Docker volume configured in .env."
docker compose up -d --build
echo "API: http://127.0.0.1:$(awk -F= '/^AWM_PORT=/{print $2}' .env)"
echo "Review .env and docs/deployment.md for local model setup and backup/restore."
