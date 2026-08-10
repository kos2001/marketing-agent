from __future__ import annotations
import json
from typing import Any, Protocol

import httpx


class ChatClient(Protocol):
    async def chat(self, system: str, user: str, *, session_id: str) -> str: ...


class HttpChatClient:
    """OpenAI-compatible client (hermes-gateway or any /v1/chat/completions host)."""

    def __init__(self, base_url: str, api_key: str, model: str, timeout_s: float = 120.0):
        self._base = base_url.rstrip("/")
        self._key = api_key
        self._model = model
        self._timeout = timeout_s

    async def chat(self, system: str, user: str, *, session_id: str) -> str:
        headers = {
            "Authorization": f"Bearer {self._key}",
            "Content-Type": "application/json",
            "X-Session-Id": session_id,
        }
        body = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(f"{self._base}/chat/completions", headers=headers, json=body)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"] or ""


def extract_json(raw: str) -> Any:
    """Extract the first top-level JSON object/array from a possibly noisy LLM response."""
    start = None
    for i, ch in enumerate(raw):
        if ch in "{[":
            start = i
            break
    if start is None:
        raise ValueError(f"JSON을 찾을 수 없음: {raw[:120]}")
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(raw)):
        ch = raw[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch in "{[":
            depth += 1
        elif ch in "}]":
            depth -= 1
            if depth == 0:
                return json.loads(raw[start : i + 1])
    raise ValueError(f"JSON이 닫히지 않음: {raw[:120]}")
