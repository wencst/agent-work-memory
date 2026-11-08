#!/usr/bin/env sh
set -eu

if [ ! -f .env ]; then
  cp .env.example .env
  key=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
  # Replace the template key without requiring GNU-specific sed flags.
  KEY="$key" python3 - <<'PY'
import os
from pathlib import Path
p = Path('.env')
s = p.read_text()
s = s.replace('replace-with-a-random-secret-at-least-24-characters', os.environ['KEY'])
p.write_text(s)
PY
  echo "Created .env with a generated API key. Keep it secret; it grants access to all data in this personal instance."
fi

echo "Starting Agent Work Memory (API + worker). Data is stored in the Docker volume configured in .env."
docker compose up -d --build
echo "API: http://127.0.0.1:$(awk -F= '/^AWM_PORT=/{print $2}' .env)"
echo "Review .env and docs/deployment.md for local model setup and backup/restore."
