from __future__ import annotations

import os
import time
from datetime import datetime, timezone

from .cli import apply_retention, process_once
from .config import Settings


def run() -> None:
    settings = Settings.from_env()
    interval = int(os.getenv("AWM_RETENTION_INTERVAL_SECONDS", "3600"))
    if interval < 60:
        raise RuntimeError("AWM_RETENTION_INTERVAL_SECONDS must be at least 60")
    next_retention = 0.0
    print("AWM worker started; event extraction and retention are enabled.", flush=True)
    while True:
        now = time.monotonic()
        if now >= next_retention:
            count = apply_retention(settings)
            if count:
                print(f"Expired raw content for {count} event(s) at {datetime.now(timezone.utc).isoformat()}", flush=True)
            next_retention = now + interval
        if process_once(settings) == 0:
            time.sleep(2)


if __name__ == "__main__":
    run()
