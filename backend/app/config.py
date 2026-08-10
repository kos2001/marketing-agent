from __future__ import annotations
import os
from dataclasses import dataclass


@dataclass
class Settings:
    db_path: str
    llm_base_url: str
    llm_api_key: str
    llm_model: str

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            db_path=os.environ.get("MA_DB_PATH", "data/marketing_agent.db"),
            llm_base_url=os.environ.get("MA_LLM_BASE_URL", "http://localhost:8700/v1"),
            llm_api_key=os.environ.get("MA_LLM_API_KEY", ""),
            llm_model=os.environ.get("MA_LLM_MODEL", "marketing-agent"),
        )
