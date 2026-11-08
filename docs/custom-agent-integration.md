# Custom agent integration examples

Any CLI or desktop agent that can make an HTTP request can integrate without a native plugin. The event API is the canonical v1 interface; see [`integration-contract.md`](integration-contract.md) for field semantics and adapter requirements.

## cURL (portable smoke test)

```bash
export AWM_BASE_URL=http://127.0.0.1:8765
export AWM_API_KEY='your-instance-key'

curl --fail-with-body --silent --show-error \
  -H "Authorization: Bearer $AWM_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{
    "source":"internal-agent",
    "session_id":"desktop-session-2026-04-15-001",
    "event_type":"task.completed",
    "occurred_at":"2026-04-15T10:20:30Z",
    "client_event_id":"stable-event-uuid-001",
    "content":"Implemented retry handling in src/client.py. The change was committed as abc123.",
    "metadata":{"repository":"payments-api","branch":"feature/retries"}
  }' \
  "$AWM_BASE_URL/v1/events"
```

Do not submit an event called `task.completed` unless the agent has reliable evidence that the task completed. Prefer tool results, a diff, or commit metadata over a generated narrative.

## Python SDK-style helper

```python
import os
import time
import uuid
from datetime import datetime, timezone

import requests

BASE_URL = os.environ.get("AWM_BASE_URL", "http://127.0.0.1:8765").rstrip("/")
API_KEY = os.environ["AWM_API_KEY"]
SOURCE = "internal-agent"


def record_event(session_id: str, event_type: str, content: str, metadata: dict | None = None) -> str:
    # Generate the event ID once and persist/reuse it if retrying the same event.
    event_id = str(uuid.uuid4())
    payload = {
        "source": SOURCE,
        "session_id": session_id,
        "event_type": event_type,
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "client_event_id": event_id,
        "content": content,
        "metadata": metadata or {},
    }
    for attempt in range(3):
        try:
            response = requests.post(
                f"{BASE_URL}/v1/events",
                json=payload,
                headers={"Authorization": f"Bearer {API_KEY}"},
                timeout=3,
            )
            response.raise_for_status()
            return response.json()["id"]
        except requests.RequestException:
            if attempt == 2:
                raise
            time.sleep(0.25 * (2**attempt))
    raise RuntimeError("unreachable")
```

For production adapters, create and persist the idempotency ID at event creation, not inside a function that may be re-entered during retry. Do not block the agent's primary task indefinitely: use a bounded local queue and expose an adapter warning if AWM is unavailable.

## Desktop application

A desktop agent can post events through its plugin/hook API or a small local companion process. Configure the companion with the local AWM base URL and API key through the OS secret store where possible. Capture only the selected lifecycle events; avoid blindly uploading full transcripts, environment variables, credentials, or unrelated files. The event API is not CORS-based browser API and should not be called directly from an untrusted web page.

## Reading approved memories

Agent clients can search approved memories with:

```bash
curl --get --fail-with-body \
  -H "Authorization: Bearer $AWM_API_KEY" \
  --data-urlencode 'q=retry handling' \
  "$AWM_BASE_URL/v1/search"
```

Pending and rejected candidates are never returned by `/v1/search`.
