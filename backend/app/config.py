from __future__ import annotations
import os
from dataclasses import dataclass


@dataclass
class Settings:
    db_path: str
    llm_base_url: str
    llm_api_key: str
    llm_model: str
    llm_timeout_s: float
    seed_demo_data: bool

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            db_path=os.environ.get("MA_DB_PATH", "data/marketing_agent.db"),
            llm_base_url=os.environ.get("MA_LLM_BASE_URL", "http://localhost:8700/v1"),
            llm_api_key=os.environ.get("MA_LLM_API_KEY", ""),
            llm_model=os.environ.get("MA_LLM_MODEL", "marketing-agent"),
            # 종합(SUMMARY/STRATEGY) 에이전트는 원문 전체 + 여러 산출을 한 번에
            # 종합하므로 진단 에이전트보다 오래 걸린다 — 기본 120s는 이 머신에서
            # 다른 프로파일과 LLM 처리량을 나누는 상황에서 ReadTimeout을 냈다.
            llm_timeout_s=float(os.environ.get("MA_LLM_TIMEOUT_S", "300")),
            # 저장소가 비어 있을 때 데모 리포트를 채워 첫 화면이 비어 보이지
            # 않게 한다. 실 데이터가 하나라도 들어오면 다시 채우지 않는다
            # (app/demo_fixture.py의 seed_demo_data 참고).
            seed_demo_data=os.environ.get("MA_SEED_DEMO_DATA", "1") != "0",
        )
