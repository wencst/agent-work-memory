# Agent Work Memory

**An evidence-first, self-hosted work memory for AI agents.** Capture events from coding agents, turn them into reviewable memory candidates, and make approved facts available to later sessions—with a traceable source for every claim.

> **Status: early MVP / not production-ready.** This first version provides a personal, single-owner API, an OpenCode event adapter, an optional local-model extraction worker, and an integration contract for other agents. The Codex and Claude Code adapters, multi-user access control, and production hardening are not implemented yet.

## Why this project exists

Conversation transcripts are not reliable memories. “We should upgrade PostgreSQL” is not evidence that an upgrade happened. Agent Work Memory stores source events separately from extracted claims. Claims remain **pending review** until a person approves them, and each claim must cite a verbatim excerpt from its source event.

## MVP scope

- Personal, single-owner installation. API-key holders share that owner's memory; this is **not** a multi-user/team service.
- OpenCode adapter is the first integration, currently experimental and limited to events available to the plugin hook.
- A documented, versioned HTTP event contract for Codex, Claude Code, desktop agents, and custom agents.
- Local-first inference: extraction is performed only when the worker is explicitly run. Default model endpoint is loopback (`http://127.0.0.1:11434/v1`).
- Raw event content is retained for 30 days by default; configure `AWM_RAW_RETENTION_DAYS` to change this. Expiration clears raw content but retains source metadata and reviewed memory records.
- Extracted claims are not searchable by agents until approved.
- MIT licensed.

## Quick start: Docker Compose

Requires Docker Engine with Compose v2 and Python 3 for generating a secret.

```bash
git clone https://github.com/wencst/agent-work-memory.git
cd agent-work-memory
./scripts/compose-up.sh
```

The helper creates `.env` with a random API key, then builds and starts the API and background worker. API: `http://127.0.0.1:8765`. Agent data and SQLite storage persist in the named volume `agent-work-memory-data`. See [`docs/deployment.md`](docs/deployment.md) for backup/restore, retention, model setup, and alternate deployment modes.

To add a bundled, local Ollama model (first run downloads model weights):

```bash
./scripts/compose-local-llm.sh
```

The optional Ollama model files persist in a separate named volume. For air-gapped environments, preload and mirror all required images and weights. No installation mode can be assumed offline until network egress is blocked and tested.

## Quick start: Python

Requires Python 3.11+.

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
export AWM_API_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
awm serve
```

In another terminal with the same environment, run `awm worker` to process events and enforce retention. The default database is `~/.local/share/agent-work-memory/memory.sqlite3`.

## Connect OpenCode

See [`integrations/opencode/README.md`](integrations/opencode/README.md). The adapter is experimental; validate the actual events emitted by your OpenCode version before using it with sensitive work.

## Add a custom CLI or desktop agent

Any agent able to issue HTTP requests can use the stable v1 event contract. See [`docs/custom-agent-integration.md`](docs/custom-agent-integration.md) for cURL, Python, desktop companion, idempotency, and approved-memory retrieval examples. Codex and Claude Code native adapters are planned after OpenCode validation.

## Review candidates

```bash
# Use the API key from .env for Docker Compose deployments.
curl -H "Authorization: Bearer $AWM_API_KEY" \
  'http://127.0.0.1:8765/v1/memories?status=pending'

curl -X POST -H "Authorization: Bearer $AWM_API_KEY" -H 'Content-Type: application/json' \
  -d '{"action":"approve"}' \
  http://127.0.0.1:8765/v1/memories/MEMORY_ID/review
```

Only approved claims are returned by `/v1/search`.

## Design principles

1. **Evidence before assertion.** Every extracted claim cites its source event and an exact quote.
2. **Discussion is not execution.** Claims are typed and require human approval before recall.
3. **Keep the source and the memory separate.** Raw event text has a configurable retention period; a reviewed claim can outlive it with its source metadata and evidence excerpt.
4. **No silent cloud calls.** The server has no hosted model default and performs no inference on event submission.
5. **Keep integrations replaceable.** Agent-specific adapters implement the same HTTP contract; MCP can be added as another access surface.
6. **Personal first.** Do not mistake one API key for multi-tenant authorization. Team/project sharing is explicitly out of scope for this MVP.

See [`docs/architecture.md`](docs/architecture.md), [`docs/integration-contract.md`](docs/integration-contract.md), [`docs/security-and-privacy.md`](docs/security-and-privacy.md), and [`docs/deployment.md`](docs/deployment.md).

## Development

```bash
pip install -e '.[dev]'
pytest
```

## Roadmap

- [x] Personal evidence/event API and SQLite storage
- [x] 30-day configurable raw-content retention
- [x] Candidate memory review and approved-memory retrieval
- [x] OpenCode experimental plugin
- [x] Versioned HTTP integration contract and custom-agent examples
- [x] Docker Compose deployment with persistent volumes and worker-managed retention
- [ ] Verify and improve OpenCode capture coverage against supported versions
- [ ] Codex adapter
- [ ] Generic SDK and Claude Code adapter
- [ ] MCP server and desktop-friendly review UI
- [ ] Authentication suitable for remote deployment, audit logging, backups, and operational hardening
- [ ] Evaluate Hindsight / Graphiti as replaceable memory backends against a project-work benchmark

Contributions and adapter implementations are welcome. Read the integration contract first so adapters preserve event IDs, timestamps, source identity, and provenance.
