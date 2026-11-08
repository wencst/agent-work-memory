# Deployment guide

Agent Work Memory is personal/single-owner software in its current MVP. The API key grants access to the entire instance. Do not expose it as a shared multi-user service.

## Recommended setup for local deployments

Use separate keys for management and agent traffic:

```dotenv
AWM_ADMIN_API_KEY=admin-token-with-at-least-24-characters
AWM_AGENT_API_KEYS=agent-token-1,agent-token-2
```

The admin token is intended for review, event inspection, and memory approval. Agent tokens are limited to posting new events and searching approved memories. When `AWM_AGENT_API_KEYS` is empty, the project falls back to a legacy single-key mode, which is less safe.

## Option 1: One-command Docker Compose (API + worker)

Requirements: Docker Engine with Compose v2 and Python 3 for the setup helper.

```bash
git clone https://github.com/wencst/agent-work-memory.git
cd agent-work-memory
chmod +x scripts/compose-up.sh
./scripts/compose-up.sh
```

The helper creates `.env` with random secrets if they are missing. It does not automatically create separate agent tokens; edit `.env` before starting the stack if you want least privilege.

## Option 2: Compose with bundled local Ollama

```bash
./scripts/compose-local-llm.sh
```

You should still set both `AWM_ADMIN_API_KEY` and `AWM_AGENT_API_KEYS` in `.env` before starting the overlay.

## Networking and security

- The published API port binds to `127.0.0.1` by default. Do not change `AWM_BIND_ADDRESS` to `0.0.0.0` without adding TLS, an appropriate identity/access layer, and a threat review.
- The current admin token and agent tokens are not per-user isolation. Anyone who has the admin key can access the whole personal store.
- The health endpoint is intentionally unauthenticated and returns only service status/version.
- Pin image versions and audit dependencies before a production rollout. For an offline network, mirror the container base image, Python dependencies, model image, and weights internally.
- Apply host firewall/egress controls if the deployment must not access the public internet.

## Troubleshooting

- **API key rejected**: ensure adapters use the exact admin or agent token from `.env` and restart Compose after changing it.
- **No extraction candidates**: check `docker compose logs -f worker`; verify the model endpoint is reachable from the worker container and supports the requested JSON response format.
- **No data after recreation**: confirm the same named volume remains configured; do not use `down -v`.
