from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from agent_work_memory.api import create_app
from agent_work_memory.config import Settings
from agent_work_memory.db import connect


def make_settings(tmp_path: Path) -> Settings:
    return Settings(api_key="x" * 32, database_path=tmp_path / "test.db")


def auth() -> dict[str, str]:
    return {"Authorization": f"Bearer {'x' * 32}"}


def test_event_requires_key_and_is_idempotent(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    client = TestClient(create_app(settings))
    payload = {
        "source": "opencode", "session_id": "s1", "event_type": "tool.after",
        "occurred_at": datetime.now(timezone.utc).isoformat(), "content": "Changed auth middleware",
        "metadata": {}, "client_event_id": "event-1",
    }
    assert client.post("/v1/events", json=payload).status_code == 401
    first = client.post("/v1/events", json=payload, headers=auth())
    second = client.post("/v1/events", json=payload, headers=auth())
    assert first.status_code == 201
    assert second.json()["status"] == "duplicate"
    assert second.json()["id"] == first.json()["id"]


def test_only_approved_memories_are_searchable(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    client = TestClient(create_app(settings))
    event = client.post("/v1/events", headers=auth(), json={
        "source": "test", "session_id": "s1", "event_type": "note",
        "occurred_at": datetime.now(timezone.utc).isoformat(), "content": "We chose PostgreSQL for the event store.",
    }).json()
    conn = connect(settings.database_path)
    conn.execute(
        "INSERT INTO memories(id,event_id,kind,claim,evidence_quote,confidence,status,created_at) VALUES(?,?,?,?,?,?,?,?)",
        ("m1", event["id"], "decision", "We chose PostgreSQL for the event store.", "chose PostgreSQL", 0.9, "pending", datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    conn.close()
    query = {"q": "PostgreSQL"}
    assert client.get("/v1/search", params=query, headers=auth()).json()["items"] == []
    reviewed = client.post("/v1/memories/m1/review", headers=auth(), json={"action": "approve"})
    assert reviewed.json()["status"] == "approved"
    assert len(client.get("/v1/search", params=query, headers=auth()).json()["items"]) == 1


def test_retention_clears_raw_content_only(tmp_path: Path) -> None:
    from datetime import timedelta
    from agent_work_memory.cli import apply_retention

    settings = make_settings(tmp_path)
    conn = connect(settings.database_path)
    old = (datetime.now(timezone.utc) - timedelta(days=40)).isoformat()
    conn.execute(
        "INSERT INTO events(id,source,session_id,event_type,occurred_at,received_at,content) VALUES(?,?,?,?,?,?,?)",
        ("e1", "test", "s1", "note", old, old, "raw secret text"),
    )
    conn.commit()
    conn.close()
    assert apply_retention(settings) == 1
    conn = connect(settings.database_path)
    row = conn.execute("SELECT content,expired_at FROM events WHERE id='e1'").fetchone()
    conn.close()
    assert row["content"] is None
    assert row["expired_at"] is not None
