#!/usr/bin/env sh
set -eu

if [ ! -f .env ]; then
  echo "Missing .env. Run ./scripts/compose-up.sh first or copy .env.example to .env." >&2
  exit 1
fi

# Optional profile adds Ollama, downloads the configured local model, and points
# the extraction worker at it. Model weights persist in a separate named volume.
docker compose -f compose.yaml -f compose.local-llm.yaml up -d --build
