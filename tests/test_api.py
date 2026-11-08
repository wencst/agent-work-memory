from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, Field

from .config import Settings
from .db import connect, json_object, row_dict


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


class EventIn(BaseModel):
    source: str = Field(min_length=1, max_length=80)
    session_id: str = Field(min_length=1, max_length=200)
    event_type: str = Field(min_length=1, max_length=120)
    occurred_at: datetime
    content: str = Field(min_length=1, max_length=100_000)
    metadata: dict = Field(default_factory=dict)
    client_event_id: str | None = Field(default=None, max_length=200)


class ReviewIn(BaseModel):
    action: Literal["approve", "reject"]


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    app = FastAPI(title="Agent Work Memory", version="0.1.0", docs_url=None, redoc_url=None)
    conn = connect(settings.database_path)
    conn.close()

    def resolve_scope(authorization: str | None) -> str:
        supplied = authorization.removeprefix("Bearer ") if authorization else ""
        if not supplied:
            raise HTTPException(status_code=401, detail="Missing Bearer token")
        if supplied == settings.admin_api_key:
            return "admin"
        if supplied in settings.agent_api_keys:
            return "agent"
        raise HTTPException(status_code=401, detail="Invalid API key")

    def require_scope(*allowed_scopes: str):
        def dependency(authorization: str | None = Header(default=None)) -> str:
            scope = resolve_scope(authorization)
            if allowed_scopes and scope not in allowed_scopes:
                raise HTTPException(status_code=403, detail="Token scope does not allow this operation")
            return scope

        return dependency

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "version": "0.1.0"}

    @app.post("/v1/events", dependencies=[Depends(require_scope("agent", "admin"))], status_code=201)
    def ingest_event(body: EventIn) -> dict:
        event_id = str(uuid.uuid4())
        received_at = utcnow()
        conn = connect(settings.database_path)
        try:
            if body.client_event_id:
                existing = conn.execute(
                    "SELECT id FROM events WHERE source=? AND client_event_id=?", (body.source, body.client_event_id)
                ).fetchone()
                if existing:
                    return {"id": existing["id"], "status": "duplicate"}
            conn.execute(
                "INSERT INTO events(id,client_event_id,source,session_id,event_type,occurred_at,received_at,content,metadata_json) "
                "VALUES(?,?,?,?,?,?,?,?,?)",
                (event_id, body.client_event_id, body.source, body.session_id, body.event_type,
                 iso(body.occurred_at), iso(received_at), body.content, json_object(body.metadata)),
            )
            conn.commit()
        finally:
            conn.close()
        return {"id": event_id, "status": "accepted", "received_at": iso(received_at)}

    @app.get("/v1/events/{event_id}", dependencies=[Depends(require_scope("admin")]) )
    def get_event(event_id: str) -> dict:
        conn = connect(settings.database_path)
        try:
            row = conn.execute("SELECT * FROM events WHERE id=?", (event_id,)).fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="Event not found")
            return row_dict(row)
        finally:
            conn.close()

    @app.get("/v1/memories", dependencies=[Depends(require_scope("admin") )])
    def list_memories(status: Literal["pending", "approved", "rejected"] | None = Query(default=None), limit: int = Query(default=50, ge=1, le=200)) -> dict:
        conn = connect(settings.database_path)
        try:
            if status:
                rows = conn.execute(
                    "SELECT m.*, e.source, e.session_id, e.event_type, e.occurred_at, e.expired_at "
                    "FROM memories m JOIN events e ON e.id=m.event_id WHERE m.status=? ORDER BY m.created_at DESC LIMIT ?",
                    (status, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT m.*, e.source, e.session_id, e.event_type, e.occurred_at, e.expired_at "
                    "FROM memories m JOIN events e ON e.id=m.event_id ORDER BY m.created_at DESC LIMIT ?", (limit,)
                ).fetchall()
            return {"items": [row_dict(r) for r in rows]}
        finally:
            conn.close()

    @app.get("/v1/search", dependencies=[Depends(require_scope("agent", "admin") )])
    def search_memories(q: str = Query(min_length=2, max_length=500), limit: int = Query(default=10, ge=1, le=50)) -> dict:
        escaped = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        conn = connect(settings.database_path)
        try:
            rows = conn.execute(
                "SELECT m.*, e.source, e.session_id, e.event_type, e.occurred_at, e.expired_at "
                "FROM memories m JOIN events e ON e.id=m.event_id "
                "WHERE m.status='approved' AND m.claim LIKE ? ESCAPE '\\' ORDER BY m.created_at DESC LIMIT ?",
                (f"%{escaped}%", limit),
            ).fetchall()
            return {"items": [row_dict(r) for r in rows]}
        finally:
            conn.close()

    @app.post("/v1/memories/{memory_id}/review", dependencies=[Depends(require_scope("admin") )])
    def review_memory(memory_id: str, body: ReviewIn) -> dict:
        status = "approved" if body.action == "approve" else "rejected"
        conn = connect(settings.database_path)
        try:
            cur = conn.execute(
                "UPDATE memories SET status=?, reviewed_at=? WHERE id=? AND status='pending'",
                (status, iso(utcnow()), memory_id),
            )
            conn.commit()
            if cur.rowcount != 1:
                exists = conn.execute("SELECT 1 FROM memories WHERE id=?", (memory_id,)).fetchone()
                if not exists:
                    raise HTTPException(status_code=404, detail="Memory not found")
                raise HTTPException(status_code=409, detail="Memory is no longer pending review")
            return {"id": memory_id, "status": status}
        finally:
            conn.close()

    return app
