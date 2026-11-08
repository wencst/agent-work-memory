from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    client_event_id TEXT,
    source TEXT NOT NULL,
    session_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    received_at TEXT NOT NULL,
    content TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    extraction_status TEXT NOT NULL DEFAULT 'pending',
    extraction_error TEXT,
    expired_at TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_events_source_client_id
    ON events(source, client_event_id) WHERE client_event_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_events_pending ON events(extraction_status, received_at);
CREATE INDEX IF NOT EXISTS idx_events_received ON events(received_at);
CREATE TABLE IF NOT EXISTS memories (
    id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    kind TEXT NOT NULL,
    claim TEXT NOT NULL,
    evidence_quote TEXT NOT NULL,
    confidence REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL,
    reviewed_at TEXT,
    UNIQUE(event_id, claim)
);
CREATE INDEX IF NOT EXISTS idx_memories_status ON memories(status, created_at);
"""


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    return conn


def json_object(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def row_dict(row: sqlite3.Row) -> dict[str, Any]:
    result = dict(row)
    if "metadata_json" in result:
        result["metadata"] = json.loads(result.pop("metadata_json"))
    return result
