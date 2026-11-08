from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    admin_api_key: str
    agent_api_keys: tuple[str, ...]
    database_path: Path
    raw_retention_days: int = 30
    host: str = "127.0.0.1"
    port: int = 8765
    llm_base_url: str = "http://127.0.0.1:11434/v1"
    llm_model: str = "qwen2.5:14b"
    llm_api_key: str = "local"
    llm_timeout_seconds: int = 90

    @property
    def api_key(self) -> str:
        return self.admin_api_key

    @classmethod
    def from_env(cls) -> "Settings":
        legacy_api_key = os.getenv("AWM_API_KEY", "")
        admin_key = os.getenv("AWM_ADMIN_API_KEY", legacy_api_key)
        if len(admin_key) < 24:
            raise RuntimeError("Set AWM_ADMIN_API_KEY (or AWM_API_KEY as legacy fallback) to a secret of at least 24 characters.")

        raw_agent_keys = os.getenv("AWM_AGENT_API_KEYS", "")
        if raw_agent_keys.strip():
            agent_keys = tuple(key.strip() for key in raw_agent_keys.split(",") if key.strip())
        elif legacy_api_key:
            agent_keys = (legacy_api_key,)
        else:
            agent_keys = ()
        if not agent_keys:
            agent_keys = (admin_key,)

        data_dir = Path(os.getenv("AWM_DATA_DIR", str(Path.home() / ".local/share/agent-work-memory")))
        retention = int(os.getenv("AWM_RAW_RETENTION_DAYS", "30"))
        if retention < 1:
            raise RuntimeError("AWM_RAW_RETENTION_DAYS must be at least 1.")
        return cls(
            admin_api_key=admin_key,
            agent_api_keys=agent_keys,
            database_path=Path(os.getenv("AWM_DATABASE_PATH", str(data_dir / "memory.sqlite3"))),
            raw_retention_days=retention,
            host=os.getenv("AWM_HOST", "127.0.0.1"),
            port=int(os.getenv("AWM_PORT", "8765")),
            llm_base_url=os.getenv("AWM_LLM_BASE_URL", "http://127.0.0.1:11434/v1").rstrip("/"),
            llm_model=os.getenv("AWM_LLM_MODEL", "qwen2.5:14b"),
            llm_api_key=os.getenv("AWM_LLM_API_KEY", "local"),
            llm_timeout_seconds=int(os.getenv("AWM_LLM_TIMEOUT_SECONDS", "90")),
        )
