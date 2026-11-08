# Architecture

## Scope

Version 0.1 is a personal, single-owner memory server. All agents configured with the owner's API key can write to and search that owner's memory. It does not implement users, organizations, project ACLs, or tenant isolation. Do not expose it as a shared company service.

## Components

- **Agent adapters**: OpenCode first; later Codex, Claude Code, custom desktop and CLI agents. They send source events to the HTTP contract.
- **FastAPI intake service**: authenticates one owner API key, validates bounded event payloads, and stores them in SQLite. Event submission does not call an LLM.
- **SQLite evidence store**: raw event content, source/session/time metadata, extraction status, and memory candidates. WAL mode is enabled. Raw event content expires after configurable retention; provenance rows remain.
- **Extraction worker**: a separately invoked CLI process. It requests JSON from an OpenAI-compatible endpoint; the default endpoint is local Ollama on loopback. It rejects claims without a verbatim evidence quote and creates pending candidates.
- **Review and recall API**: an owner reviews pending claims. Only approved claims are returned by `/v1/search`.

## Data flow

```text
Agent adapter -> POST /v1/events -> SQLite event (pending)
                                     |
                         `awm process` (explicit)
                                     |
                      local/OpenAI-compatible LLM
                                     |
                 evidence-checked pending candidates
                                     |
                   owner review -> approved memory
                                     |
                 GET /v1/search -> agent context
```

## Decisions and known limitations

- SQLite minimizes setup and keeps data local for a single-owner pilot. It is not a distributed database or a concurrent multi-tenant store.
- Search is keyword-only in this MVP. Embeddings, graph storage, and MCP are intentionally deferred until a project-work benchmark justifies them.
- The extractor is replaceable; no memory engine dependency is hard-wired. Hindsight and Graphiti can be evaluated behind this boundary later.
- Exact quote validation prevents unsupported citations but does not prove that the claim is a correct interpretation. Human approval remains required.
- The OpenCode adapter currently forwards hook events available to the plugin; it does not claim complete transcript coverage. Verify capture against each supported OpenCode version before relying on it.
- API key authentication is a local single-owner guard, not enterprise identity, role-based access control, or protection against a compromised host.
