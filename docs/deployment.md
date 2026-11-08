# Deployment guide

Agent Work Memory is personal/single-owner software in its current MVP. The API key grants access to the entire instance. Do not expose it as a shared multi-user service.

## Option 1: One-command Docker Compose (API + worker)

Requirements: Docker Engine with Compose v2 and Python 3 for the setup helper.

```bash
git clone https://github.com/wencst/agent-work-memory.git
cd agent-work-memory
chmod +x scripts/compose-up.sh
./scripts/compose-up.sh
```

The helper creates `.env` with a random API key on first run, builds the API image, and starts the API and background worker. The API is bound to `127.0.0.1:8765` on the host by default. Read the API key from `.env` and configure each local adapter with it. View logs with `docker compose logs -f awm worker`.

This mode uses the configured OpenAI-compatible extraction endpoint. The API does not call an LLM on event intake; the worker sends event content to `AWM_LLM_BASE_URL` when it extracts memories. The default `.env.example` endpoint is loopback. In a container, `127.0.0.1` refers to that container, so set the base URL to the address of your local model service. For fully local inference, use Option 2.

## Option 2: Compose with bundled local Ollama

This includes the Ollama service and pulls a model into a persistent volume. The first model download can be large and requires access to the image/model source. For air-gapped deployment, preload the image and model into your internal registry/cache and follow your organization's offline artifact procedure.

```bash
./scripts/compose-up.sh
./scripts/compose-local-llm.sh
```

Equivalent Compose command:

```bash
docker compose -f compose.yaml -f compose.local-llm.yaml up -d --build
```

The `agent-work-memory-data` volume stores SQLite data. The separate `agent-work-memory-ollama` volume stores model weights. Do not run `docker compose down -v` unless you intend to delete both volumes and all data. To use a different model, set `AWM_OLLAMA_MODEL` in `.env`, then restart the overlay; ensure the model supports the structured JSON output used by the extractor.

Check services:

```bash
docker compose -f compose.yaml -f compose.local-llm.yaml ps
docker compose -f compose.yaml -f compose.local-llm.yaml logs -f worker
curl http://127.0.0.1:8765/health
```

## Option 3: Existing local or approved cloud model endpoint

Keep API and worker in Compose, and edit `.env`:

```dotenv
AWM_LLM_BASE_URL=http://host.docker.internal:11434/v1
AWM_LLM_MODEL=your-local-model
AWM_LLM_API_KEY=local
```

`host.docker.internal` may need a host-gateway mapping on Linux; alternatively put the model service on a trusted Compose network and use its service DNS name. To use an approved cloud endpoint, configure its URL, model, and credential explicitly. This sends source event content to that endpoint; verify your organization's policy before doing so. Never assume that self-hosting AWM makes a cloud inference call local.

## Option 4: Run directly with Python

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install .
export AWM_API_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
export AWM_DATA_DIR="$HOME/.local/share/agent-work-memory"
awm serve
```

In another process using the same environment, run `awm worker`. The worker continuously processes pending events and enforces raw-content retention. To run it under systemd or another process manager, configure both `awm serve` and `awm worker` with the same API key and database path. Run only one worker for this MVP.

## Persistence, retention, backups

### Docker Compose

- SQLite database and event records: named volume `agent-work-memory-data`, mounted at `/data`.
- Ollama model files (optional): named volume `agent-work-memory-ollama`.
- Change volume names in `.env` before first startup. Changing the name later creates a new empty volume; it does not migrate existing data.
- Inspect volume names with `docker volume ls`.

Back up the SQLite volume while the service is stopped, or use SQLite's online backup API. Example offline backup:

```bash
docker compose stop awm worker
docker run --rm -v agent-work-memory-data:/data:ro -v "$PWD/backups:/backup" alpine \
  sh -c 'tar czf /backup/awm-data-$(date +%F-%H%M%S).tar.gz -C /data .'
docker compose start awm worker
```

Restore only after stopping services; preserve the `.env` API key and verify the restored database before resuming ingestion. Backups contain sensitive content and must be encrypted and access-controlled according to your policy.

### Retention

`AWM_RAW_RETENTION_DAYS` defaults to 30. The background worker runs retention at startup and every `AWM_RETENTION_INTERVAL_SECONDS` (default 3600, minimum 60). Expiration nulls raw event content while retaining event metadata and memory evidence quotes; it does not erase the database or approved memories. Adjust retention in `.env` and recreate services:

```bash
docker compose up -d
```

## Networking and security

- The published API port binds to `127.0.0.1` by default. Do not change `AWM_BIND_ADDRESS` to `0.0.0.0` without adding TLS, an appropriate identity/access layer, and a threat review.
- The current single API key is not per-user isolation. Anyone who has it can access the whole personal store.
- The health endpoint is intentionally unauthenticated and returns only service status/version.
- Pin image versions and audit dependencies before a production rollout. For an offline network, mirror the container base image, Python dependencies, model image, and weights internally.
- Apply host firewall/egress controls if the deployment must not access the public internet. The software's local defaults are not a network-level guarantee.

## Troubleshooting

- **API key rejected**: ensure adapters use the exact `AWM_API_KEY` in `.env`; restart Compose after changing it.
- **No extraction candidates**: check `docker compose logs -f worker`; verify the model endpoint is reachable from the worker container and supports the requested JSON response format.
- **No data after recreation**: confirm the same named volume remains configured; do not use `down -v`.
- **Raw content not expiring**: ensure the worker is healthy and check `AWM_RAW_RETENTION_DAYS`; `awm expire` can be run manually in the API image as a diagnostic.
- **OpenCode events missing**: the adapter remains experimental; inspect plugin logs and verify the OpenCode version's supported hooks.
