# OpenCode adapter (experimental)

This plugin is the first Agent Work Memory integration. It forwards OpenCode plugin lifecycle events to the configured local AWM HTTP API. The exact events exposed by OpenCode vary across versions; this adapter is experimental and does **not** claim complete conversation or tool-output capture. Inspect and test the captured event payloads before enabling it for real work.

## Setup

Install the Python server from the repository and configure it on the same machine (or trusted private network):

```bash
export AWM_API_KEY='your-long-random-secret'
awm serve
```

Build/install the plugin according to OpenCode's local plugin instructions. This source is written against the OpenCode plugin interface and imports `@opencode-ai/plugin`; install that package in the plugin's development environment and compile TypeScript before use. Configure the plugin with environment variables available to the OpenCode process:

```bash
export AWM_BASE_URL=http://127.0.0.1:8765
export AWM_API_KEY='same-secret-as-server'
```

Use the OpenCode plugin config to load `awm-plugin.ts` (or its compiled JavaScript output). Plugin packaging and automatic installation are intentionally not included in this first cut.

## Data and limitations

- The plugin posts only its observed OpenCode hook/event payload. It does not read arbitrary chat-history files.
- Event data is serialized to JSON; review what the installed OpenCode version emits to ensure it does not contain content you do not want stored.
- AWM retention defaults to clearing raw event content after 30 days. Memory candidates still require human approval.
- If AWM is unavailable, the plugin does not interrupt the agent; the event is dropped and a warning is printed locally. Durable retry is not implemented yet.
- No event body is sent to any cloud model by this adapter. The separate AWM worker sends it only to the configured extraction endpoint when explicitly run.

For other agents, implement the canonical contract in [`../../docs/integration-contract.md`](../../docs/integration-contract.md).
