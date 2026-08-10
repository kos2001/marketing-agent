from __future__ import annotations
import json


class StubChatClient:
    """세션 접두사(prefix)로 매칭해 미리 정한 JSON 문자열을 돌려주는 테스트용 클라이언트."""

    def __init__(self, responses: dict[str, dict | list | str]):
        # key: session_id prefix to match (startswith), value: python obj to json-dump (or raw str)
        self._responses = responses
        self.calls: list[tuple[str, str, str]] = []

    async def chat(self, system: str, user: str, *, session_id: str) -> str:
        self.calls.append((system, user, session_id))
        for prefix, payload in self._responses.items():
            if session_id.startswith(prefix):
                if isinstance(payload, str):
                    return payload
                return json.dumps(payload, ensure_ascii=False)
        raise KeyError(f"no stub response for session_id={session_id}")
