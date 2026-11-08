# Security and privacy (MVP)

This is an early-development personal tool. It is not yet a hardened production service.

## Data handling

- The API defaults to `127.0.0.1`; do not bind to `0.0.0.0` or publish a port without adding appropriate authentication, TLS, authorization, and operational controls.
- SQLite is stored under `~/.local/share/agent-work-memory` by default. Protect the host, filesystem, backups, and database file.
- Raw event content is retained for 30 days by default. Set `AWM_RAW_RETENTION_DAYS` to another positive number. Run `awm expire` regularly; this MVP does not schedule retention automatically.
- Expiration clears raw event content, not event metadata or evidence quotes attached to memory candidates. To erase all related data, delete the database or implement a controlled deletion workflow before production use.
- The event API and extraction worker do not log event bodies by design.

## Authentication model

For safety and least privilege, the project now supports a split-key model:

- `AWM_ADMIN_API_KEY`: review, inspect raw events, and manage memory approvals.
- `AWM_AGENT_API_KEYS`: submit agent events and search approved memories only.
- `AWM_API_KEY` remains a legacy fallback for single-key local deployments, but it is treated as the admin key for backward compatibility.

Do not reuse the admin key as an agent token. Each agent token should be distinct, revocable, and scoped to a specific integration or local session. A compromised agent token must not allow memory approval.

## Model endpoint

- No model call occurs during event intake.
- The worker uses `AWM_LLM_BASE_URL`, defaulting to `http://127.0.0.1:11434/v1`; running `awm process` sends pending event text to that endpoint.
- Configure a cloud endpoint only if policy permits sending source events there. The project cannot enforce the endpoint's data residency or provider retention terms.
- Model output is untrusted. Only candidates with an exact quote from the source event are accepted, and candidates remain pending until owner approval.

## Credentials and network

- Set a random `AWM_ADMIN_API_KEY` and distinct `AWM_AGENT_API_KEYS` values. The same key currently grants full read/write access to the single-owner store.
- Use a firewall or network namespace to enforce egress policy; a loopback default is not proof of offline operation.
- Do not put keys in the repository, event content, metadata, or logs.
- No TLS, key rotation, per-client credentials, audit log, encrypted database, backup encryption, rate limiting, or multi-user authorization is implemented in this MVP.

## Before any shared/production deployment

Add and review: proper identity and authorization; key rotation and secret management; TLS; audit trails; retention scheduling; backup/restore and deletion tests; database migration policy; rate limiting and payload limits at the reverse proxy; model endpoint allowlisting; dependency/image pinning and offline artifact verification; security testing; and tested tenant/project isolation if multi-user support is introduced.
