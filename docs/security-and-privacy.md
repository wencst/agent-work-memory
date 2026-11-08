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

## Security model

This project now supports two token classes:

- **Admin token** (`AWM_ADMIN_API_KEY`): full control, used for review, event inspection, and config-sensitive admin operations.
- **Agent token** (`AWM_AGENT_API_KEYS`): can submit events and search approved memories only. It cannot review or inspect raw events.

For a single-user local deployment, `AWM_API_KEY` still works as a legacy fallback and is treated as the admin token. For better separation, set both `AWM_ADMIN_API_KEY` and `AWM_AGENT_API_KEYS` explicitly.

## Quick start

Requires Python 3.11+.

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
export AWM_ADMIN_API_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
export AWM_AGENT_API_KEYS="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
awm serve
```

The API binds to `127.0.0.1:8765` by default. For initial setup, use the built-in OpenCode plugin described in [`integrations/opencode/README.md`](integrations/opencode/README.md). Never expose this MVP to an untrusted network.

To extract candidates, configure a local OpenAI-compatible model endpoint and run the worker explicitly:

```bash
export AWM_LLM_BASE_URL=http://127.0.0.1:11434/v1
export AWM_LLM_MODEL=qwen2.5:14b
awm process --once
```

The worker sends event content to the configured endpoint. Do not configure a public/cloud endpoint unless your data policy explicitly permits it. The API itself does not call any model provider.

Review candidates in the API:

```bash
curl -H "Authorization: Bearer $AWM_ADMIN_API_KEY" http://127.0.0.1:8765/v1/memories?status=pending
curl -X POST -H "Authorization: Bearer $AWM_ADMIN_API_KEY" -H 'Content-Type: application/json' \
  -d '{"action":"approve"}' http://127.0.0.1:8765/v1/memories/MEMORY_ID/review
```

An agent token is intended for event submission and memory lookup only:

```bash
curl -H "Authorization: Bearer $AWM_AGENT_API_KEYS" \
  -H 'Content-Type: application/json' \
  -d '{"source":"internal-agent","session_id":"demo","event_type":"task.completed","occurred_at":"2026-11-08T09:00:00Z","content":"Implemented retry handling","metadata":{"repository":"demo"},"client_event_id":"demo-001"}' \
  http://127.0.0.1:8765/v1/events
```

## Design principles

1. **Evidence before assertion.** Every extracted claim cites its source event and an exact quote.
2. **Discussion is not execution.** Claims are typed and require human approval before recall.
3. **Keep the source and the memory separate.** Raw event text has a configurable retention period; a reviewed claim can outlive it with its source metadata and evidence excerpt.
4. **No silent cloud calls.** The server has no hosted model default and performs no inference on event submission.
5. **Keep integrations replaceable.** Agent-specific adapters implement the same HTTP contract; MCP can be added as another access surface.
6. **Personal first, least privilege second.** An admin key is separate from agent keys, and agent keys do not have review or raw-event access.

See [`docs/architecture.md`](docs/architecture.md), [`docs/integration-contract.md`](docs/integration-contract.md), and [`docs/security-and-privacy.md`](docs/security-and-privacy.md).

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
- [x] Local-first, explicitly invoked extraction worker
- [x] Split admin and agent API keys
- [ ] Verify and improve OpenCode capture coverage against supported versions
- [ ] Codex adapter
- [ ] Generic SDK and Claude Code adapter
- [ ] MCP server and desktop-friendly review UI
- [ ] Authentication suitable for remote deployment, audit logging, backups, and operational hardening
- [ ] Evaluate Hindsight / Graphiti as replaceable memory backends against a project-work benchmark

Contributions and adapter implementations are welcome. Read the integration contract first so adapters preserve event IDs, timestamps, source identity, and provenance.
