from __future__ import annotations

import argparse
import json
import time
import uuid
from datetime import datetime, timedelta, timezone

from .config import Settings
from .db import connect
from .extractor import ExtractionError, extract_candidates


def process_once(settings: Settings) -> int:
    conn = connect(settings.database_path)
    try:
        event = conn.execute(
            "SELECT id, content FROM events WHERE extraction_status='pending' AND content IS NOT NULL ORDER BY received_at LIMIT 1"
        ).fetchone()
        if event is None:
            return 0
        try:
            candidates = extract_candidates(
                event["content"], base_url=settings.llm_base_url, model=settings.llm_model,
                api_key=settings.llm_api_key, timeout=settings.llm_timeout_seconds,
            )
            now = datetime.now(timezone.utc).isoformat()
            for candidate in candidates:
                conn.execute(
                    "INSERT OR IGNORE INTO memories(id,event_id,kind,claim,evidence_quote,confidence,status,created_at) "
                    "VALUES(?,?,?,?,?,?,?,?)",
                    (str(uuid.uuid4()), event["id"], candidate.kind, candidate.claim, candidate.evidence_quote,
                     candidate.confidence, "pending", now),
                )
            conn.execute("UPDATE events SET extraction_status='processed', extraction_error=NULL WHERE id=?", (event["id"],))
            conn.commit()
            return 1
        except ExtractionError as exc:
            conn.execute("UPDATE events SET extraction_status='failed', extraction_error=? WHERE id=?", (str(exc), event["id"]))
            conn.commit()
            return 0
    finally:
        conn.close()


def apply_retention(settings: Settings) -> int:
    cutoff = (datetime.now(timezone.utc) - timedelta(days=settings.raw_retention_days)).isoformat()
    conn = connect(settings.database_path)
    try:
        cur = conn.execute(
            "UPDATE events SET content=NULL, expired_at=? WHERE content IS NOT NULL AND received_at < ?",
            (datetime.now(timezone.utc).isoformat(), cutoff),
        )
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(prog="awm")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("serve", help="Run the local HTTP API")
    process = sub.add_parser("process", help="Extract pending memory candidates using the configured model endpoint")
    process.add_argument("--once", action="store_true", help="Process at most one event and exit")
    sub.add_parser("expire", help="Clear raw event content past the configured retention period")
    args = parser.parse_args()
    settings = Settings.from_env()
    if args.command == "serve":
        import uvicorn
        uvicorn.run("agent_work_memory.api:create_app", factory=True, host=settings.host, port=settings.port)
    elif args.command == "process":
        if args.once:
            print(json.dumps({"processed": process_once(settings)}))
        else:
            while True:
                if process_once(settings) == 0:
                    time.sleep(2)
    elif args.command == "expire":
        print(json.dumps({"expired_raw_events": apply_retention(settings)}))


if __name__ == "__main__":
    main()
