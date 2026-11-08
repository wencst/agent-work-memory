from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    api_key: str
    database_path: Path
    raw_retention_days: int = 30
    host: str = "127.0.0.1"
    port: int = 8765
    llm_base_url: str = "http://127.0.0.1:11434/v1"
    llm_model: str = "qwen2.5:14b"
    llm_api_key: str = "local"
    llm_timeout_seconds: int = 90

    @classmethod
    def from_env(cls) -> "Settings":
        api_key = os.getenv("AWM_API_KEY", "")
        if len(api_key) < 24:
            raise RuntimeError("Set AWM_API_KEY to a secret of at least 24 characters.")
        data_dir = Path(os.getenv("AWM_DATA_DIR", str(Path.home() / ".local/share/agent-work-memory")))
        retention = int(os.getenv("AWM_RAW_RETENTION_DAYS", "30"))
        if retention < 1:
            raise RuntimeError("AWM_RAW_RETENTION_DAYS must be at least 1.")
        return cls(
            api_key=api_key,
            database_path=Path(os.getenv("AWM_DATABASE_PATH", str(data_dir / "memory.sqlite3"))),
            raw_retention_days=retention,
            host=os.getenv("AWM_HOST", "127.0.0.1"),
            port=int(os.getenv("AWM_PORT", "8765")),
            llm_base_url=os.getenv("AWM_LLM_BASE_URL", "http://127.0.0.1:11434/v1").rstrip("/"),
            llm_model=os.getenv("AWM_LLM_MODEL", "qwen2.5:14b"),
            llm_api_key=os.getenv("AWM_LLM_API_KEY", "local"),
            llm_timeout_seconds=int(os.getenv("AWM_LLM_TIMEOUT_SECONDS", "90")),
        )
