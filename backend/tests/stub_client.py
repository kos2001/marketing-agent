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
        matches = [p for p in self._responses if session_id.startswith(p)]
        if not matches:
            raise KeyError(f"no stub response for session_id={session_id}")
        # 가장 구체적인(가장 긴) 접두사가 이긴다 — "v"와 "v2"처럼 한쪽이 다른 쪽의
        # 접두사인 경우 삽입 순서에 따라 잘못 매칭되는 것을 막는다.
        best = max(matches, key=len)
        payload = self._responses[best]
        if isinstance(payload, str):
            return payload
        return json.dumps(payload, ensure_ascii=False)
