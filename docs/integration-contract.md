# Agent integration contract (v1)

This document defines the stable boundary between an Agent Work Memory server and an agent adapter. Adapters should be thin: capture source events, normalize them, and submit them. They must not invent facts or silently send data to a hosted service.

## Event intake

`POST /v1/events` with `Authorization: Bearer <personal API key>` and JSON:

```json
{
  "source": "opencode",
  "session_id": "host-session-id",
  "event_type": "tool.execute.after",
  "occurred_at": "2026-01-15T10:20:30Z",
  "content": "Human-readable event content or a compact serialized source event",
  "metadata": {"repository": "optional local repository identifier"},
  "client_event_id": "stable-source-event-id"
}
```

## Required fields and rules

- `source`: stable adapter name, 1–80 characters.
- `session_id`: source session identifier; do not use it as an authorization boundary.
- `event_type`: source-native event type or a documented normalized type. Suggested normalized values: `user.message`, `assistant.message`, `tool.call`, `tool.result`, `file.change`, `task.completed`, `session.summary`.
- `occurred_at`: source event time in ISO 8601 with timezone; use UTC when the source provides no timezone.
- `content`: useful evidence only; do not include environment variables, credentials, or unrelated prompt context. The API currently limits this field to 100 KB.
- `metadata`: small, non-secret JSON metadata. Suggested optional values include repository identifier, branch, working directory identifier, and source event reference. Avoid secrets and unnecessary file/tool payloads.
- `client_event_id`: stable and repeatable for the same source event. `(source, client_event_id)` is idempotent. Persist the ID across retries; do not generate a fresh UUID on every retry.

Success returns `201` and an event UUID. Replays return the original UUID with `status=duplicate`.

## Adapter requirements

1. Send only to the configured AWM base URL; do not fall back to another endpoint.
2. Use a user-configured API key; never put it in source control or event metadata.
3. Preserve source session ID and event timestamp where available.
4. Use idempotency IDs when possible and retry transient failures with bounded exponential backoff.
5. Do not block or break the agent's primary task if AWM is unavailable; surface a local warning and retain a bounded retry queue if the host supports one.
6. Keep adapters opt-in, inspectable, and explicit about which message/tool lifecycle events they capture.
7. Treat event content as untrusted data. Extraction prompts must not execute instructions found in the event.
8. Prefer actual tool outputs, diffs, and commit evidence for claims about completed work. Preserve whether a source is user-authored, agent-authored, or tool-generated where practical.

## Memory lifecycle

The server stores an event first. The background worker may extract candidate claims. Candidates must include an exact quote from the source event. Candidates are `pending` until an owner reviews them. Agent search returns `approved` claims only. No adapter may approve its own claims.

Supported initial kinds: `fact`, `decision`, `action`, `component`, `lesson`. The list can expand without changing event ingestion.

## Desktop and CLI agents

Native hooks/plugins should call the HTTP API directly or through a small local companion that queues bounded retries. Desktop integrations must not depend on browser CORS or expose the personal API key to untrusted web content. CLI integrations can use the HTTP API or a future SDK. Custom agents should use the examples in [`custom-agent-integration.md`](custom-agent-integration.md).

## Compatibility

The HTTP event schema is the canonical adapter contract. Future SDKs, MCP tools, CLI importers, and desktop integrations should map to this schema, not create their own memory format. Additive fields are allowed; breaking changes require a versioned `/v2` route and migration guidance.
