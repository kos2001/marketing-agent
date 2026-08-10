# marketing-agent MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Working end-to-end web app: upload marketing/sales material → multi-agent diagnosis pipeline (grounded, cross-verified) → 현황진단 + 타임라인 + Action Items report, viewable in a Next.js dashboard.

**Architecture:** FastAPI backend (SQLite) running an async agent pipeline behind a pluggable `ChatClient` protocol (real HTTP client for hermes-gateway/OpenAI-compatible endpoints, stub client for tests) + Next.js frontend dashboard. Adapted from `~/gitspace/weekly-report-harness` per `docs/superpowers/specs/2026-08-11-marketing-agent-design.md`.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic, SQLite (stdlib `sqlite3`), httpx, pytest, pytest-asyncio; Next.js (App Router) + TypeScript, fetch-based API client, vitest.

## Global Constraints

- No live LLM/network calls in tests — all agent/pipeline tests use a stub `ChatClient`.
- Every diagnosis/opportunity/risk/critical-point item carries a `citations: list[str]` field verified against source text — never trust unverified quotes.
- Ambiguous/unknown judgments must be written as `판단근거없음`, never silently omitted or marked "없음".
- Two agents disagreeing → both verdicts kept and shown, never silently resolved.
- `AGENT_CATALOG`-style declared `needs` per agent; a test must assert the orchestrator only runs an agent after its declared deps resolve.
- Backend runs standalone with `uvicorn app.main:app`; frontend with `npm run dev`, calling backend via `NEXT_PUBLIC_API_BASE`.

---

## Task 1: Backend scaffolding + schemas

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/app/__init__.py`
- Create: `backend/app/schemas.py`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/test_schemas.py`

**Interfaces:**
- Produces: Pydantic models `SourceDoc(id, cycle_id, title, text)`, `Citation(quote, source_id)`, `DiagnosisItem(id, channel, summary, strength_or_weakness, citations: list[Citation], status: Literal["draft"])`, `OpportunityRiskItem(id, kind: Literal["opportunity","risk"], title, rationale, citations: list[Citation])`, `CriticalPoint(id, title, impact, urgency, decision_needed, citations: list[Citation])`, `TimelineLink(item_title, prior_cycle_id, same_issue: bool, rebuttal_passed: bool)`, `ActionItem(id, title, owner: str, due: str, priority: Literal["high","mid","low"], source_item_ids: list[str])`, `VerifiedStatus = Literal["confirmed","needs_review","unfounded"]`.

- [ ] **Step 1: Init backend project**

```bash
mkdir -p backend/app backend/tests
cd backend && cat > pyproject.toml << 'EOF'
[project]
name = "marketing-agent-backend"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "fastapi>=0.110",
  "uvicorn[standard]>=0.29",
  "pydantic>=2.6",
  "httpx>=0.27",
]

[project.optional-dependencies]
dev = ["pytest>=8", "pytest-asyncio>=0.23"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
EOF
touch app/__init__.py tests/__init__.py
```

- [ ] **Step 2: Write schemas.py**

```python
# backend/app/schemas.py
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field

VerifiedStatus = Literal["confirmed", "needs_review", "unfounded"]


class SourceDoc(BaseModel):
    id: str
    cycle_id: str
    title: str
    text: str


class Citation(BaseModel):
    quote: str
    source_id: str


class DiagnosisItem(BaseModel):
    id: str
    channel: str
    summary: str
    kind: Literal["strength", "weakness"]
    citations: list[Citation] = Field(default_factory=list)
    status: VerifiedStatus = "needs_review"


class OpportunityRiskItem(BaseModel):
    id: str
    kind: Literal["opportunity", "risk"]
    title: str
    rationale: str
    citations: list[Citation] = Field(default_factory=list)
    additionally_flagged: bool = False


class CriticalPoint(BaseModel):
    id: str
    title: str
    impact: str
    urgency: str
    decision_needed: str
    citations: list[Citation] = Field(default_factory=list)


class TimelineLink(BaseModel):
    item_title: str
    prior_cycle_id: str
    same_issue: bool
    rebuttal_passed: bool
    repeat_count: int = 1


class ActionItem(BaseModel):
    id: str
    title: str
    owner: str
    due: str
    priority: Literal["high", "mid", "low"]
    source_item_ids: list[str] = Field(default_factory=list)


class CycleReport(BaseModel):
    cycle_id: str
    diagnosis: list[DiagnosisItem] = Field(default_factory=list)
    opportunities_risks: list[OpportunityRiskItem] = Field(default_factory=list)
    critical_points: list[CriticalPoint] = Field(default_factory=list)
    timeline: list[TimelineLink] = Field(default_factory=list)
    action_items: list[ActionItem] = Field(default_factory=list)
    overview: str = ""
    overview_warnings: list[str] = Field(default_factory=list)
    coverage_note: str = ""
```

- [ ] **Step 3: Write test**

```python
# backend/tests/test_schemas.py
from app.schemas import DiagnosisItem, Citation


def test_diagnosis_item_defaults_needs_review():
    item = DiagnosisItem(id="d1", channel="이메일", summary="오픈율 하락", kind="weakness")
    assert item.status == "needs_review"
    assert item.citations == []


def test_diagnosis_item_with_citation():
    item = DiagnosisItem(
        id="d1", channel="이메일", summary="오픈율 하락", kind="weakness",
        citations=[Citation(quote="오픈율이 12%로 하락", source_id="s1")],
    )
    assert item.citations[0].source_id == "s1"
```

- [ ] **Step 4: Run tests**

```bash
cd backend && python -m venv .venv && .venv/bin/pip install -e ".[dev]" -q
.venv/bin/pytest tests/test_schemas.py -v
```
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/pyproject.toml backend/app/__init__.py backend/app/schemas.py backend/tests/__init__.py backend/tests/test_schemas.py
git commit -m "feat: backend scaffolding and core schemas"
```

---

## Task 2: ChatClient protocol + stub + grounding utility

**Files:**
- Create: `backend/app/llm.py`
- Create: `backend/app/grounding.py`
- Create: `backend/tests/test_grounding.py`
- Create: `backend/tests/stub_client.py`

**Interfaces:**
- Consumes: nothing new.
- Produces: `class ChatClient(Protocol): async def chat(self, system: str, user: str, *, session_id: str) -> str`; `class HttpChatClient(ChatClient)` (real, hermes-gateway/OpenAI-compatible); `ground_citations(citations: list[Citation], sources: dict[str, str]) -> list[Citation]` (drops citations whose quote is not a verbatim substring of `sources[source_id]`); `StubChatClient` in tests returning canned JSON per call count, for use by all later agent tests.

- [ ] **Step 1: Write failing test for grounding**

```python
# backend/tests/test_grounding.py
from app.schemas import Citation
from app.grounding import ground_citations


def test_ground_citations_keeps_verbatim_match():
    sources = {"s1": "이번 달 오픈율이 12%로 하락했다."}
    citations = [Citation(quote="오픈율이 12%로 하락", source_id="s1")]
    result = ground_citations(citations, sources)
    assert len(result) == 1


def test_ground_citations_drops_fabricated_quote():
    sources = {"s1": "이번 달 오픈율이 12%로 하락했다."}
    citations = [
        Citation(quote="오픈율이 12%로 하락", source_id="s1"),
        Citation(quote="전환율이 300% 상승", source_id="s1"),
    ]
    result = ground_citations(citations, sources)
    assert len(result) == 1
    assert result[0].quote == "오픈율이 12%로 하락"


def test_ground_citations_unknown_source_dropped():
    citations = [Citation(quote="아무 말", source_id="missing")]
    assert ground_citations(citations, {}) == []
```

- [ ] **Step 2: Run to verify fail**

```bash
cd backend && .venv/bin/pytest tests/test_grounding.py -v
```
Expected: FAIL (`app.grounding` not found)

- [ ] **Step 3: Implement llm.py and grounding.py**

```python
# backend/app/llm.py
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
```

```python
# backend/app/grounding.py
from __future__ import annotations
from .schemas import Citation


def ground_citations(citations: list[Citation], sources: dict[str, str]) -> list[Citation]:
    """원문과 축자 대조해 실재하지 않는 인용을 인용 단위로 제거한다."""
    kept: list[Citation] = []
    for c in citations:
        text = sources.get(c.source_id)
        if text and c.quote.strip() and c.quote in text:
            kept.append(c)
    return kept
```

- [ ] **Step 4: Add stub client for later agent tests**

```python
# backend/tests/stub_client.py
from __future__ import annotations
import json


class StubChatClient:
    """세션 접두사(prefix)로 매칭해 미리 정한 JSON 문자열을 돌려주는 테스트용 클라이언트."""

    def __init__(self, responses: dict[str, dict | list]):
        # key: session_id prefix to match (startswith), value: python obj to json-dump
        self._responses = responses
        self.calls: list[tuple[str, str, str]] = []

    async def chat(self, system: str, user: str, *, session_id: str) -> str:
        self.calls.append((system, user, session_id))
        for prefix, payload in self._responses.items():
            if session_id.startswith(prefix):
                return json.dumps(payload, ensure_ascii=False)
        raise KeyError(f"no stub response for session_id={session_id}")
```

- [ ] **Step 5: Run tests to verify pass**

```bash
cd backend && .venv/bin/pytest tests/test_grounding.py -v
```
Expected: PASS (3 tests)

- [ ] **Step 6: Commit**

```bash
git add backend/app/llm.py backend/app/grounding.py backend/tests/test_grounding.py backend/tests/stub_client.py
git commit -m "feat: chat client abstraction, JSON extraction, citation grounding"
```

---

## Task 3: Storage layer (SQLite)

**Files:**
- Create: `backend/app/storage.py`
- Create: `backend/tests/test_storage.py`

**Interfaces:**
- Consumes: `SourceDoc`, `CycleReport` from `app.schemas`.
- Produces: `class Store`: `__init__(self, path: str)`; `add_source(doc: SourceDoc) -> None`; `sources_for_cycle(cycle_id: str) -> list[SourceDoc]`; `save_report(report: CycleReport) -> None`; `get_report(cycle_id: str) -> CycleReport | None`; `list_cycles() -> list[str]` (chronological by insertion); `prior_cycles(cycle_id: str) -> list[str]` (cycles before this one, chronological).

- [ ] **Step 1: Write failing test**

```python
# backend/tests/test_storage.py
import tempfile, os
from app.storage import Store
from app.schemas import SourceDoc, CycleReport, DiagnosisItem


def make_store():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    return Store(path)


def test_add_and_fetch_sources():
    store = make_store()
    store.add_source(SourceDoc(id="s1", cycle_id="2026-W32", title="이메일 성과", text="오픈율 12%"))
    docs = store.sources_for_cycle("2026-W32")
    assert len(docs) == 1
    assert docs[0].text == "오픈율 12%"


def test_save_and_get_report_roundtrip():
    store = make_store()
    report = CycleReport(
        cycle_id="2026-W32",
        diagnosis=[DiagnosisItem(id="d1", channel="이메일", summary="하락", kind="weakness")],
    )
    store.save_report(report)
    fetched = store.get_report("2026-W32")
    assert fetched is not None
    assert fetched.diagnosis[0].summary == "하락"


def test_prior_cycles_chronological():
    store = make_store()
    for cid in ["2026-W30", "2026-W31", "2026-W32"]:
        store.save_report(CycleReport(cycle_id=cid))
    assert store.prior_cycles("2026-W32") == ["2026-W30", "2026-W31"]
```

- [ ] **Step 2: Run to verify fail**

```bash
cd backend && .venv/bin/pytest tests/test_storage.py -v
```
Expected: FAIL (`app.storage` not found)

- [ ] **Step 3: Implement storage.py**

```python
# backend/app/storage.py
from __future__ import annotations
import sqlite3
from .schemas import SourceDoc, CycleReport


class Store:
    def __init__(self, path: str):
        self._conn = sqlite3.connect(path)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS sources ("
            "id TEXT PRIMARY KEY, cycle_id TEXT, title TEXT, text TEXT)"
        )
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS reports ("
            "cycle_id TEXT PRIMARY KEY, seq INTEGER, data TEXT)"
        )
        self._conn.commit()

    def add_source(self, doc: SourceDoc) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO sources (id, cycle_id, title, text) VALUES (?, ?, ?, ?)",
            (doc.id, doc.cycle_id, doc.title, doc.text),
        )
        self._conn.commit()

    def sources_for_cycle(self, cycle_id: str) -> list[SourceDoc]:
        rows = self._conn.execute(
            "SELECT id, cycle_id, title, text FROM sources WHERE cycle_id = ?", (cycle_id,)
        ).fetchall()
        return [SourceDoc(id=r[0], cycle_id=r[1], title=r[2], text=r[3]) for r in rows]

    def save_report(self, report: CycleReport) -> None:
        seq_row = self._conn.execute("SELECT COALESCE(MAX(seq), 0) FROM reports").fetchone()
        existing = self._conn.execute(
            "SELECT seq FROM reports WHERE cycle_id = ?", (report.cycle_id,)
        ).fetchone()
        seq = existing[0] if existing else seq_row[0] + 1
        self._conn.execute(
            "INSERT OR REPLACE INTO reports (cycle_id, seq, data) VALUES (?, ?, ?)",
            (report.cycle_id, seq, report.model_dump_json()),
        )
        self._conn.commit()

    def get_report(self, cycle_id: str) -> CycleReport | None:
        row = self._conn.execute(
            "SELECT data FROM reports WHERE cycle_id = ?", (cycle_id,)
        ).fetchone()
        return CycleReport.model_validate_json(row[0]) if row else None

    def list_cycles(self) -> list[str]:
        rows = self._conn.execute("SELECT cycle_id FROM reports ORDER BY seq ASC").fetchall()
        return [r[0] for r in rows]

    def prior_cycles(self, cycle_id: str) -> list[str]:
        row = self._conn.execute(
            "SELECT seq FROM reports WHERE cycle_id = ?", (cycle_id,)
        ).fetchone()
        if not row:
            return [c for c in self.list_cycles() if c != cycle_id]
        rows = self._conn.execute(
            "SELECT cycle_id FROM reports WHERE seq < ? ORDER BY seq ASC", (row[0],)
        ).fetchall()
        return [r[0] for r in rows]
```

- [ ] **Step 4: Run tests to verify pass**

```bash
cd backend && .venv/bin/pytest tests/test_storage.py -v
```
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/app/storage.py backend/tests/test_storage.py
git commit -m "feat: SQLite storage for sources and cycle reports"
```

---

## Task 4: Diagnosis agents D1–D3 + verification V, V2

**Files:**
- Create: `backend/app/agents_diagnosis.py`
- Create: `backend/tests/test_agents_diagnosis.py`

**Interfaces:**
- Consumes: `ChatClient` (Task 2), `SourceDoc` (Task 1), `ground_citations` (Task 2), `extract_json` (Task 2).
- Produces: `async def run_d1(client, sources: list[SourceDoc]) -> list[DiagnosisItem]`; `async def run_d2(client, sources) -> list[OpportunityRiskItem]`; `async def run_d3(client, sources) -> list[CriticalPoint]`; `async def run_v(client, sources, d1_items: list[DiagnosisItem]) -> list[DiagnosisItem]` (returns d1_items with `status` updated: independently re-derives, marks `confirmed` if re-derived set has matching channel+kind, else `needs_review`); `async def run_v2(client, sources, d2_items: list[OpportunityRiskItem]) -> list[OpportunityRiskItem]` (returns *additional* items found by V2 not already in d2_items by title, with `additionally_flagged=True`).

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/test_agents_diagnosis.py
import pytest
from app.schemas import SourceDoc, DiagnosisItem, OpportunityRiskItem
from app.agents_diagnosis import run_d1, run_d2, run_d3, run_v, run_v2
from tests.stub_client import StubChatClient

SOURCES = [SourceDoc(id="s1", cycle_id="c1", title="이메일", text="이번 달 오픈율이 12%로 하락했다.")]


@pytest.mark.asyncio
async def test_run_d1_parses_items_and_grounds_citations():
    client = StubChatClient({
        "d1": {"items": [
            {"channel": "이메일", "summary": "오픈율 하락", "kind": "weakness",
             "citations": [{"quote": "오픈율이 12%로 하락", "source_id": "s1"},
                            {"quote": "지어낸 문장", "source_id": "s1"}]}
        ]}
    })
    items = await run_d1(client, SOURCES)
    assert len(items) == 1
    assert len(items[0].citations) == 1  # 지어낸 인용은 그라운딩에서 제거됨
    assert items[0].channel == "이메일"


@pytest.mark.asyncio
async def test_run_v_confirms_matching_reappraisal():
    d1_items = [DiagnosisItem(id="d1-1", channel="이메일", summary="오픈율 하락", kind="weakness")]
    client = StubChatClient({
        "v": {"items": [{"channel": "이메일", "kind": "weakness", "summary": "재도출"}]}
    })
    result = await run_v(client, SOURCES, d1_items)
    assert result[0].status == "confirmed"


@pytest.mark.asyncio
async def test_run_v_needs_review_when_not_matched():
    d1_items = [DiagnosisItem(id="d1-1", channel="이메일", summary="오픈율 하락", kind="weakness")]
    client = StubChatClient({"v": {"items": []}})
    result = await run_v(client, SOURCES, d1_items)
    assert result[0].status == "needs_review"


@pytest.mark.asyncio
async def test_run_v2_flags_only_missing_items():
    d2_items = [OpportunityRiskItem(id="o1", kind="risk", title="오픈율 하락", rationale="r")]
    client = StubChatClient({
        "v2": {"items": [
            {"kind": "risk", "title": "오픈율 하락", "rationale": "r"},
            {"kind": "risk", "title": "구독 해지 증가", "rationale": "r2"},
        ]}
    })
    additional = await run_v2(client, SOURCES, d2_items)
    assert len(additional) == 1
    assert additional[0].title == "구독 해지 증가"
    assert additional[0].additionally_flagged is True
```

- [ ] **Step 2: Run to verify fail**

```bash
cd backend && .venv/bin/pytest tests/test_agents_diagnosis.py -v
```
Expected: FAIL (`app.agents_diagnosis` not found)

- [ ] **Step 3: Implement agents_diagnosis.py**

```python
# backend/app/agents_diagnosis.py
from __future__ import annotations
import uuid
from .llm import ChatClient, extract_json
from .grounding import ground_citations
from .schemas import SourceDoc, DiagnosisItem, Citation, OpportunityRiskItem, CriticalPoint

D1_SYSTEM = (
    "당신은 영업/마케팅 현황진단관입니다. 주어진 원문 자료만 근거로 채널·캠페인별 "
    "강점과 약점을 찾아 JSON으로만 답하십시오. 형식: "
    '{"items": [{"channel": str, "summary": str, "kind": "strength"|"weakness", '
    '"citations": [{"quote": str, "source_id": str}]}]}. '
    "quote는 원문에서 그대로 축자 인용해야 합니다. 근거 없는 문장은 만들지 마십시오."
)

D2_SYSTEM = (
    "당신은 영업/마케팅 기회·리스크 정리관입니다. 원문만 근거로 사업 임팩트가 큰 "
    '기회와 리스크를 뽑아 JSON으로만 답하십시오. 형식: {"items": [{"kind": '
    '"opportunity"|"risk", "title": str, "rationale": str, "citations": [{"quote": str, '
    '"source_id": str}]}]}.'
)

D3_SYSTEM = (
    "당신은 Critical Point 도출관입니다. 방치하면 치명적인 관리 포인트와 필요한 "
    '결정을 원문 근거로 찾아 JSON으로만 답하십시오. 형식: {"items": [{"title": str, '
    '"impact": str, "urgency": str, "decision_needed": str, "citations": [{"quote": str, '
    '"source_id": str}]}]}.'
)

V_SYSTEM = (
    "당신은 독립 교차검증관입니다. 다른 에이전트의 결과를 보지 않고, 원문만으로 "
    '채널별 강점·약점을 다시 도출하십시오. JSON: {"items": [{"channel": str, '
    '"summary": str, "kind": "strength"|"weakness"}]}.'
)

V2_SYSTEM = (
    "당신은 독립 교차검증관입니다. 다른 에이전트의 결과를 보지 않고, 원문만으로 "
    '기회·리스크를 다시 도출하십시오. JSON: {"items": [{"kind": "opportunity"|"risk", '
    '"title": str, "rationale": str}]}.'
)


def _sources_text(sources: list[SourceDoc]) -> str:
    return "\n\n".join(f"[{s.id}] {s.title}\n{s.text}" for s in sources)


def _source_map(sources: list[SourceDoc]) -> dict[str, str]:
    return {s.id: s.text for s in sources}


async def run_d1(client: ChatClient, sources: list[SourceDoc]) -> list[DiagnosisItem]:
    raw = await client.chat(D1_SYSTEM, _sources_text(sources), session_id="d1")
    data = extract_json(raw)
    smap = _source_map(sources)
    items: list[DiagnosisItem] = []
    for it in data.get("items", []):
        citations = [Citation(**c) for c in it.get("citations", [])]
        items.append(DiagnosisItem(
            id=f"d1-{uuid.uuid4().hex[:8]}",
            channel=it["channel"],
            summary=it["summary"],
            kind=it["kind"],
            citations=ground_citations(citations, smap),
        ))
    return items


async def run_d2(client: ChatClient, sources: list[SourceDoc]) -> list[OpportunityRiskItem]:
    raw = await client.chat(D2_SYSTEM, _sources_text(sources), session_id="d2")
    data = extract_json(raw)
    smap = _source_map(sources)
    items: list[OpportunityRiskItem] = []
    for it in data.get("items", []):
        citations = [Citation(**c) for c in it.get("citations", [])]
        items.append(OpportunityRiskItem(
            id=f"d2-{uuid.uuid4().hex[:8]}",
            kind=it["kind"],
            title=it["title"],
            rationale=it["rationale"],
            citations=ground_citations(citations, smap),
        ))
    return items


async def run_d3(client: ChatClient, sources: list[SourceDoc]) -> list[CriticalPoint]:
    raw = await client.chat(D3_SYSTEM, _sources_text(sources), session_id="d3")
    data = extract_json(raw)
    smap = _source_map(sources)
    items: list[CriticalPoint] = []
    for it in data.get("items", []):
        citations = [Citation(**c) for c in it.get("citations", [])]
        items.append(CriticalPoint(
            id=f"d3-{uuid.uuid4().hex[:8]}",
            title=it["title"],
            impact=it["impact"],
            urgency=it["urgency"],
            decision_needed=it["decision_needed"],
            citations=ground_citations(citations, smap),
        ))
    return items


async def run_v(
    client: ChatClient, sources: list[SourceDoc], d1_items: list[DiagnosisItem]
) -> list[DiagnosisItem]:
    raw = await client.chat(V_SYSTEM, _sources_text(sources), session_id="v")
    data = extract_json(raw)
    redetected = {(it["channel"], it["kind"]) for it in data.get("items", [])}
    out = []
    for item in d1_items:
        status = "confirmed" if (item.channel, item.kind) in redetected else "needs_review"
        out.append(item.model_copy(update={"status": status}))
    return out


async def run_v2(
    client: ChatClient, sources: list[SourceDoc], d2_items: list[OpportunityRiskItem]
) -> list[OpportunityRiskItem]:
    raw = await client.chat(V2_SYSTEM, _sources_text(sources), session_id="v2")
    data = extract_json(raw)
    existing_titles = {it.title for it in d2_items}
    additional = []
    for it in data.get("items", []):
        if it["title"] not in existing_titles:
            additional.append(OpportunityRiskItem(
                id=f"v2-{uuid.uuid4().hex[:8]}",
                kind=it["kind"],
                title=it["title"],
                rationale=it["rationale"],
                additionally_flagged=True,
            ))
    return additional
```

- [ ] **Step 4: Run tests to verify pass**

```bash
cd backend && .venv/bin/pytest tests/test_agents_diagnosis.py -v
```
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/app/agents_diagnosis.py backend/tests/test_agents_diagnosis.py
git commit -m "feat: D1-D3 diagnosis agents and V/V2 cross-verification"
```

---

## Task 5: Timeline agent (T1) with rebuttal check

**Files:**
- Create: `backend/app/agents_timeline.py`
- Create: `backend/tests/test_agents_timeline.py`

**Interfaces:**
- Consumes: `ChatClient`; `DiagnosisItem`, `OpportunityRiskItem`, `CriticalPoint` from Task 1; `Store.prior_cycles`/`get_report` from Task 3.
- Produces: `async def run_t1(client, cycle_id: str, current_titles: list[str], prior_cycle_titles: dict[str, list[str]]) -> list[TimelineLink]` — for each current title, asks the LLM whether it matches any prior-cycle title (candidate match), then asks a **second, rebuttal** prompt to argue it's actually different; keeps the link only if the rebuttal fails to convince (`rebuttal_passed=True` means "survived the rebuttal / stays linked").

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/test_agents_timeline.py
import pytest
from app.agents_timeline import run_t1
from tests.stub_client import StubChatClient


@pytest.mark.asyncio
async def test_t1_links_same_issue_surviving_rebuttal():
    client = StubChatClient({
        "t1-match": {"matches": [{"current": "오픈율 하락", "prior_cycle": "c0", "prior_title": "오픈율 하락 추세"}]},
        "t1-rebut": {"same_issue": True},
    })
    links = await run_t1(client, "c1", ["오픈율 하락"], {"c0": ["오픈율 하락 추세"]})
    assert len(links) == 1
    assert links[0].same_issue is True
    assert links[0].rebuttal_passed is True


@pytest.mark.asyncio
async def test_t1_drops_link_when_rebuttal_succeeds():
    client = StubChatClient({
        "t1-match": {"matches": [{"current": "제품 사양 불일치", "prior_cycle": "c0", "prior_title": "매출 인식 불일치"}]},
        "t1-rebut": {"same_issue": False},
    })
    links = await run_t1(client, "c1", ["제품 사양 불일치"], {"c0": ["매출 인식 불일치"]})
    assert links == []


@pytest.mark.asyncio
async def test_t1_no_prior_cycles_returns_empty():
    client = StubChatClient({"t1-match": {"matches": []}})
    links = await run_t1(client, "c1", ["새 이슈"], {})
    assert links == []
```

- [ ] **Step 2: Run to verify fail**

```bash
cd backend && .venv/bin/pytest tests/test_agents_timeline.py -v
```
Expected: FAIL (`app.agents_timeline` not found)

- [ ] **Step 3: Implement agents_timeline.py**

```python
# backend/app/agents_timeline.py
from __future__ import annotations
from .llm import ChatClient, extract_json
from .schemas import TimelineLink

MATCH_SYSTEM = (
    "현재 회차 이슈 제목들과 과거 회차 이슈 제목들을 비교해, 같은 사안으로 보이는 "
    '후보 쌍을 고르십시오. JSON: {"matches": [{"current": str, "prior_cycle": str, '
    '"prior_title": str}]}. 확실하지 않으면 포함하지 마십시오.'
)

REBUTTAL_SYSTEM = (
    "두 이슈 제목이 같은 사안이라는 주장에 대해, 그것이 실은 서로 다른 사안이라는 "
    '반박을 시도하십시오. 반박이 설득력 있으면 same_issue를 false로, 반박하지 '
    '못하면 true로 답하십시오. JSON: {"same_issue": bool}.'
)


async def run_t1(
    client: ChatClient,
    cycle_id: str,
    current_titles: list[str],
    prior_cycle_titles: dict[str, list[str]],
) -> list[TimelineLink]:
    if not current_titles or not prior_cycle_titles:
        return []
    prior_text = "\n".join(
        f"[{cid}] " + ", ".join(titles) for cid, titles in prior_cycle_titles.items()
    )
    user = f"현재 회차 이슈:\n{', '.join(current_titles)}\n\n과거 회차 이슈:\n{prior_text}"
    raw = await client.chat(MATCH_SYSTEM, user, session_id="t1-match")
    matches = extract_json(raw).get("matches", [])

    links: list[TimelineLink] = []
    for m in matches:
        rebut_user = (
            f"주장: '{m['current']}' (현재 회차)와 '{m['prior_title']}' ({m['prior_cycle']} 회차)"
            "는 같은 사안이다. 이 주장을 반박하라."
        )
        raw2 = await client.chat(REBUTTAL_SYSTEM, rebut_user, session_id="t1-rebut")
        same = extract_json(raw2).get("same_issue", False)
        if same:
            links.append(TimelineLink(
                item_title=m["current"],
                prior_cycle_id=m["prior_cycle"],
                same_issue=True,
                rebuttal_passed=True,
            ))
    return links
```

- [ ] **Step 4: Run tests to verify pass**

```bash
cd backend && .venv/bin/pytest tests/test_agents_timeline.py -v
```
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/app/agents_timeline.py backend/tests/test_agents_timeline.py
git commit -m "feat: T1 timeline continuity agent with rebuttal verification"
```

---

## Task 6: Action Items agent + V3 overview fact-check

**Files:**
- Create: `backend/app/agents_actions.py`
- Create: `backend/tests/test_agents_actions.py`

**Interfaces:**
- Consumes: `ChatClient`; schemas from Task 1.
- Produces: `async def run_action_items(client, diagnosis, opp_risks, critical_points) -> list[ActionItem]`; `async def run_overview(client, diagnosis, opp_risks, critical_points, timeline, sources: dict[str,str]) -> tuple[str, list[str]]` (returns `(overview_text, warnings)`; V3 checks each overview sentence against citations already present on the items — if a sentence has no supporting citation among the grounded items, it's added to `warnings` and the overview is regenerated once with that feedback; if still unsupported after retry, keep the warning).

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/test_agents_actions.py
import pytest
from app.schemas import DiagnosisItem, OpportunityRiskItem, CriticalPoint
from app.agents_actions import run_action_items, run_overview
from tests.stub_client import StubChatClient

DIAG = [DiagnosisItem(id="d1", channel="이메일", summary="오픈율 하락", kind="weakness")]
OPP = [OpportunityRiskItem(id="o1", kind="risk", title="구독 해지 증가", rationale="r")]
CP: list[CriticalPoint] = []


@pytest.mark.asyncio
async def test_run_action_items_parses_and_links_sources():
    client = StubChatClient({
        "actions": {"items": [
            {"title": "이메일 제목 A/B 테스트 실시", "owner": "마케팅팀", "due": "2026-08-25",
             "priority": "high", "source_item_ids": ["d1"]}
        ]}
    })
    items = await run_action_items(client, DIAG, OPP, CP)
    assert len(items) == 1
    assert items[0].owner == "마케팅팀"
    assert items[0].source_item_ids == ["d1"]


@pytest.mark.asyncio
async def test_run_overview_passes_when_grounded():
    client = StubChatClient({
        "overview": "이메일 오픈율이 하락했다.",
        "v3-check": {"unsupported_sentences": []},
    })
    text, warnings = await run_overview(client, DIAG, OPP, CP, [], {})
    assert text == "이메일 오픈율이 하락했다."
    assert warnings == []


@pytest.mark.asyncio
async def test_run_overview_warns_after_failed_retry():
    calls = {"n": 0}

    class FlakyClient(StubChatClient):
        async def chat(self, system, user, *, session_id):
            if session_id.startswith("overview"):
                return "근거 없는 주장이 포함된 총평이다."
            if session_id.startswith("v3-check"):
                import json
                return json.dumps({"unsupported_sentences": ["근거 없는 주장이 포함된 총평이다."]})
            raise KeyError(session_id)

    client = FlakyClient({})
    text, warnings = await run_overview(client, DIAG, OPP, CP, [], {})
    assert len(warnings) == 1
```

- [ ] **Step 2: Run to verify fail**

```bash
cd backend && .venv/bin/pytest tests/test_agents_actions.py -v
```
Expected: FAIL (`app.agents_actions` not found)

- [ ] **Step 3: Implement agents_actions.py**

```python
# backend/app/agents_actions.py
from __future__ import annotations
import uuid
from .llm import ChatClient, extract_json
from .schemas import DiagnosisItem, OpportunityRiskItem, CriticalPoint, TimelineLink, ActionItem

ACTIONS_SYSTEM = (
    "당신은 실행 전환관입니다. 현황진단·기회·리스크·Critical Point를 바탕으로 실행 "
    '가능한 Action Item을 담당·기한·우선순위와 함께 만드십시오. JSON: {"items": '
    '[{"title": str, "owner": str, "due": "YYYY-MM-DD", "priority": "high"|"mid"|"low", '
    '"source_item_ids": [str]}]}. source_item_ids는 입력으로 준 항목의 id를 그대로 쓰십시오.'
)

OVERVIEW_SYSTEM = (
    "당신은 총평 작성관입니다. 주어진 현황진단·기회·리스크·Critical Point·타임라인을 "
    "종합해 3~5문장의 총평을 한국어로 쓰십시오. 텍스트만 출력하고 근거 없는 수치나 "
    "주장을 만들지 마십시오."
)

V3_SYSTEM = (
    "당신은 총평 사실검증관입니다. 총평의 각 문장이 제공된 근거로 뒷받침되는지 "
    '확인하십시오. 근거 없는 문장을 그대로 나열하십시오. JSON: {"unsupported_sentences": '
    "[str]}."
)


def _input_summary(diag, opp, cp) -> str:
    lines = [f"[{i.id}] {i.channel}: {i.summary} ({i.kind})" for i in diag]
    lines += [f"[{i.id}] {i.kind}: {i.title} - {i.rationale}" for i in opp]
    lines += [f"[{i.id}] CP: {i.title} - {i.impact}/{i.urgency}" for i in cp]
    return "\n".join(lines)


async def run_action_items(
    client: ChatClient,
    diagnosis: list[DiagnosisItem],
    opp_risks: list[OpportunityRiskItem],
    critical_points: list[CriticalPoint],
) -> list[ActionItem]:
    user = _input_summary(diagnosis, opp_risks, critical_points)
    raw = await client.chat(ACTIONS_SYSTEM, user, session_id="actions")
    data = extract_json(raw)
    return [
        ActionItem(
            id=f"ai-{uuid.uuid4().hex[:8]}",
            title=it["title"],
            owner=it["owner"],
            due=it["due"],
            priority=it["priority"],
            source_item_ids=it.get("source_item_ids", []),
        )
        for it in data.get("items", [])
    ]


async def run_overview(
    client: ChatClient,
    diagnosis: list[DiagnosisItem],
    opp_risks: list[OpportunityRiskItem],
    critical_points: list[CriticalPoint],
    timeline: list[TimelineLink],
    sources: dict[str, str],
) -> tuple[str, list[str]]:
    base_input = _input_summary(diagnosis, opp_risks, critical_points)
    timeline_text = "\n".join(f"{t.item_title}: {t.prior_cycle_id} 회차부터 이어짐" for t in timeline)
    text = await client.chat(OVERVIEW_SYSTEM, f"{base_input}\n\n{timeline_text}", session_id="overview")

    check_raw = await client.chat(V3_SYSTEM, f"근거:\n{base_input}\n\n총평:\n{text}", session_id="v3-check")
    unsupported = extract_json(check_raw).get("unsupported_sentences", [])
    if not unsupported:
        return text, []

    retry_text = await client.chat(
        OVERVIEW_SYSTEM,
        f"{base_input}\n\n{timeline_text}\n\n(직전 총평의 다음 문장이 근거 없다는 지적을 "
        f"받았다. 근거 있는 내용으로 다시 쓰십시오: {unsupported})",
        session_id="overview:retry1",
    )
    check_raw2 = await client.chat(
        V3_SYSTEM, f"근거:\n{base_input}\n\n총평:\n{retry_text}", session_id="v3-check:retry1"
    )
    unsupported2 = extract_json(check_raw2).get("unsupported_sentences", [])
    return retry_text, unsupported2
```

- [ ] **Step 4: Run tests to verify pass**

```bash
cd backend && .venv/bin/pytest tests/test_agents_actions.py -v
```
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/app/agents_actions.py backend/tests/test_agents_actions.py
git commit -m "feat: action items generator and V3 overview fact-check"
```

---

## Task 7: Orchestrator (declared-needs DAG)

**Files:**
- Create: `backend/app/orchestrator.py`
- Create: `backend/tests/test_orchestrator.py`

**Interfaces:**
- Consumes: everything from Tasks 1–6, `Store` from Task 3.
- Produces: `AGENT_CATALOG: tuple[dict, ...]` (ids: D1,D2,D3,V,V2,T1,ACTIONS,V3 with `needs` tuples matching the design spec table); `async def run_pipeline(client: ChatClient, store: Store, cycle_id: str) -> CycleReport` — runs D1/D2/D3/V/V2 concurrently (V needs D1's items only as input to compare against, but starts independently per catalog: needs=()), then T1 (needs D1,V,D2,D3), then ACTIONS and V3 (needs T1 + D1,D2,D3); saves and returns `CycleReport`.

- [ ] **Step 1: Write failing test asserting DAG order**

```python
# backend/tests/test_orchestrator.py
import pytest
from app.orchestrator import AGENT_CATALOG, run_pipeline
from app.storage import Store
from app.schemas import SourceDoc
from tests.stub_client import StubChatClient
import tempfile, os


def make_store():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    return Store(path)


def test_catalog_declares_needs_matching_spec():
    by_id = {a["id"]: a for a in AGENT_CATALOG}
    assert by_id["D1"]["needs"] == ()
    assert by_id["V"]["needs"] == ()
    assert set(by_id["T1"]["needs"]) == {"D1", "V", "D2", "D3"}
    assert set(by_id["V3"]["needs"]) == {"D1", "D2", "D3", "V", "V2", "T1"}


@pytest.mark.asyncio
async def test_run_pipeline_produces_full_report():
    store = make_store()
    store.add_source(SourceDoc(id="s1", cycle_id="c1", title="이메일", text="오픈율이 12%로 하락했다."))

    responses = {
        "d1": {"items": [{"channel": "이메일", "summary": "오픈율 하락", "kind": "weakness",
                           "citations": [{"quote": "오픈율이 12%로 하락", "source_id": "s1"}]}]},
        "d2": {"items": [{"kind": "risk", "title": "구독 해지 증가", "rationale": "r", "citations": []}]},
        "d3": {"items": []},
        "v": {"items": [{"channel": "이메일", "kind": "weakness", "summary": "재도출"}]},
        "v2": {"items": []},
        "t1-match": {"matches": []},
        "actions": {"items": [{"title": "A/B 테스트", "owner": "마케팅팀", "due": "2026-08-25",
                                "priority": "high", "source_item_ids": []}]},
        "overview": "총평입니다.",
        "v3-check": {"unsupported_sentences": []},
    }
    client = StubChatClient(responses)
    report = await run_pipeline(client, store, "c1")

    assert report.cycle_id == "c1"
    assert len(report.diagnosis) == 1
    assert report.diagnosis[0].status == "confirmed"
    assert len(report.action_items) == 1
    assert store.get_report("c1") is not None
```

- [ ] **Step 2: Run to verify fail**

```bash
cd backend && .venv/bin/pytest tests/test_orchestrator.py -v
```
Expected: FAIL (`app.orchestrator` not found)

- [ ] **Step 3: Implement orchestrator.py**

```python
# backend/app/orchestrator.py
from __future__ import annotations
import asyncio
from .llm import ChatClient
from .storage import Store
from .schemas import CycleReport
from .agents_diagnosis import run_d1, run_d2, run_d3, run_v, run_v2
from .agents_timeline import run_t1
from .agents_actions import run_action_items, run_overview

AGENT_CATALOG: tuple[dict[str, object], ...] = (
    {"id": "D1", "phase": "diagnose", "needs": ()},
    {"id": "D2", "phase": "diagnose", "needs": ()},
    {"id": "D3", "phase": "diagnose", "needs": ()},
    {"id": "V", "phase": "diagnose", "needs": ()},
    {"id": "V2", "phase": "diagnose", "needs": ()},
    {"id": "T1", "phase": "timeline", "needs": ("D1", "V", "D2", "D3")},
    {"id": "ACTIONS", "phase": "compose", "needs": ("D1", "D2", "D3", "T1")},
    {"id": "V3", "phase": "compose", "needs": ("D1", "D2", "D3", "V", "V2", "T1")},
)


async def run_pipeline(client: ChatClient, store: Store, cycle_id: str) -> CycleReport:
    sources = store.sources_for_cycle(cycle_id)
    source_map = {s.id: s.text for s in sources}

    # phase: diagnose — D1/D2/D3/V(needs D1 output to compare, not to gate start)/V2 in parallel
    d1_items, d2_items, d3_items = await asyncio.gather(
        run_d1(client, sources), run_d2(client, sources), run_d3(client, sources)
    )
    verified_d1, v2_additional = await asyncio.gather(
        run_v(client, sources, d1_items), run_v2(client, sources, d2_items)
    )
    opp_risks = d2_items + v2_additional

    # phase: timeline — needs D1,V,D2,D3 (declared above)
    current_titles = [i.summary for i in verified_d1] + [i.title for i in opp_risks] + [i.title for i in d3_items]
    prior_cycle_ids = store.prior_cycles(cycle_id)
    prior_titles: dict[str, list[str]] = {}
    for pc in prior_cycle_ids:
        prior_report = store.get_report(pc)
        if prior_report:
            prior_titles[pc] = (
                [i.summary for i in prior_report.diagnosis]
                + [i.title for i in prior_report.opportunities_risks]
                + [i.title for i in prior_report.critical_points]
            )
    timeline = await run_t1(client, cycle_id, current_titles, prior_titles)

    # phase: compose — ACTIONS and V3 both need T1 + D1,D2,D3
    action_items, (overview_text, warnings) = await asyncio.gather(
        run_action_items(client, verified_d1, opp_risks, d3_items),
        run_overview(client, verified_d1, opp_risks, d3_items, timeline, source_map),
    )

    total_sources = len(sources)
    coverage_note = f"{total_sources}/{total_sources}개 자료 반영" if total_sources else "입력 자료 없음"

    report = CycleReport(
        cycle_id=cycle_id,
        diagnosis=verified_d1,
        opportunities_risks=opp_risks,
        critical_points=d3_items,
        timeline=timeline,
        action_items=action_items,
        overview=overview_text,
        overview_warnings=warnings,
        coverage_note=coverage_note,
    )
    store.save_report(report)
    return report
```

- [ ] **Step 4: Run tests to verify pass**

```bash
cd backend && .venv/bin/pytest tests/test_orchestrator.py -v
```
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/app/orchestrator.py backend/tests/test_orchestrator.py
git commit -m "feat: pipeline orchestrator with declared-needs agent DAG"
```

---

## Task 8: FastAPI app (upload, run, report, history endpoints)

**Files:**
- Create: `backend/app/config.py`
- Create: `backend/app/main.py`
- Create: `backend/tests/test_api.py`

**Interfaces:**
- Consumes: `Store`, `run_pipeline`, `HttpChatClient` from prior tasks.
- Produces: FastAPI app with routes `POST /sources` (body: `{cycle_id, title, text}` → adds a `SourceDoc`), `POST /pipeline/run?cycle_id=...` (runs pipeline, returns `CycleReport`), `GET /reports/{cycle_id}`, `GET /cycles` (list of cycle ids), `GET /health`. App state holds a module-level `Store` (path from `MA_DB_PATH` env, default `data/marketing_agent.db`) and a `ChatClient` built from `MA_LLM_BASE_URL`/`MA_LLM_API_KEY`/`MA_LLM_MODEL` env vars. Tests use `app.dependency_overrides` to inject `StubChatClient` and a temp `Store`.

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/test_api.py
import pytest
from fastapi.testclient import TestClient
import tempfile, os

from app.main import app, get_client, get_store
from app.storage import Store
from tests.stub_client import StubChatClient

RESPONSES = {
    "d1": {"items": [{"channel": "이메일", "summary": "오픈율 하락", "kind": "weakness", "citations": []}]},
    "d2": {"items": []},
    "d3": {"items": []},
    "v": {"items": []},
    "v2": {"items": []},
    "t1-match": {"matches": []},
    "actions": {"items": []},
    "overview": "총평.",
    "v3-check": {"unsupported_sentences": []},
}


@pytest.fixture
def client():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    test_store = Store(path)
    app.dependency_overrides[get_store] = lambda: test_store
    app.dependency_overrides[get_client] = lambda: StubChatClient(RESPONSES)
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_upload_and_run_pipeline(client):
    resp = client.post("/sources", json={"cycle_id": "c1", "title": "이메일", "text": "오픈율이 하락했다."})
    assert resp.status_code == 200

    run_resp = client.post("/pipeline/run", params={"cycle_id": "c1"})
    assert run_resp.status_code == 200
    body = run_resp.json()
    assert body["cycle_id"] == "c1"
    assert body["diagnosis"][0]["channel"] == "이메일"


def test_get_report_and_list_cycles(client):
    client.post("/sources", json={"cycle_id": "c1", "title": "t", "text": "오픈율이 하락했다."})
    client.post("/pipeline/run", params={"cycle_id": "c1"})

    report = client.get("/reports/c1")
    assert report.status_code == 200

    cycles = client.get("/cycles")
    assert cycles.json() == ["c1"]


def test_get_missing_report_404(client):
    resp = client.get("/reports/nope")
    assert resp.status_code == 404
```

- [ ] **Step 2: Run to verify fail**

```bash
cd backend && .venv/bin/pip install "fastapi[standard]" -q && .venv/bin/pytest tests/test_api.py -v
```
Expected: FAIL (`app.main` not found)

- [ ] **Step 3: Implement config.py and main.py**

```python
# backend/app/config.py
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
```

```python
# backend/app/main.py
from __future__ import annotations
import os
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import Settings
from .storage import Store
from .llm import ChatClient, HttpChatClient
from .schemas import SourceDoc, CycleReport
from .orchestrator import run_pipeline

app = FastAPI(title="marketing-agent")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_settings = Settings.from_env()
os.makedirs(os.path.dirname(_settings.db_path) or ".", exist_ok=True)
_store = Store(_settings.db_path)
_client = HttpChatClient(_settings.llm_base_url, _settings.llm_api_key, _settings.llm_model)


def get_store() -> Store:
    return _store


def get_client() -> ChatClient:
    return _client


class SourceIn(BaseModel):
    cycle_id: str
    title: str
    text: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/sources")
def add_source(payload: SourceIn):
    store = app.dependency_overrides.get(get_store, get_store)()
    doc = SourceDoc(id=f"s-{uuid.uuid4().hex[:8]}", cycle_id=payload.cycle_id, title=payload.title, text=payload.text)
    store.add_source(doc)
    return {"id": doc.id}


@app.post("/pipeline/run", response_model=CycleReport)
async def run(cycle_id: str):
    store = app.dependency_overrides.get(get_store, get_store)()
    client = app.dependency_overrides.get(get_client, get_client)()
    return await run_pipeline(client, store, cycle_id)


@app.get("/reports/{cycle_id}", response_model=CycleReport)
def get_report(cycle_id: str):
    store = app.dependency_overrides.get(get_store, get_store)()
    report = store.get_report(cycle_id)
    if report is None:
        raise HTTPException(status_code=404, detail="report not found")
    return report


@app.get("/cycles")
def list_cycles():
    store = app.dependency_overrides.get(get_store, get_store)()
    return store.list_cycles()
```

- [ ] **Step 4: Run tests to verify pass**

```bash
cd backend && .venv/bin/pytest tests/test_api.py -v
```
Expected: PASS (4 tests)

- [ ] **Step 5: Run full backend test suite**

```bash
cd backend && .venv/bin/pytest -v
```
Expected: all tests PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/config.py backend/app/main.py backend/tests/test_api.py
git commit -m "feat: FastAPI app with sources/pipeline/reports/cycles endpoints"
```

---

## Task 9: Frontend scaffolding + API client

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/next.config.ts`
- Create: `frontend/app/layout.tsx`
- Create: `frontend/app/globals.css`
- Create: `frontend/lib/api.ts`
- Create: `frontend/lib/api.test.ts`
- Create: `frontend/vitest.config.ts`

**Interfaces:**
- Produces: TS types `SourceDoc`, `Citation`, `DiagnosisItem`, `OpportunityRiskItem`, `CriticalPoint`, `TimelineLink`, `ActionItem`, `CycleReport` (mirroring `backend/app/schemas.py`); functions `addSource(cycleId, title, text): Promise<{id: string}>`, `runPipeline(cycleId): Promise<CycleReport>`, `getReport(cycleId): Promise<CycleReport | null>`, `listCycles(): Promise<string[]>`, all reading `process.env.NEXT_PUBLIC_API_BASE` (default `http://localhost:8001`).

- [ ] **Step 1: Scaffold Next.js project files**

```bash
mkdir -p frontend/app frontend/lib
cat > frontend/package.json << 'EOF'
{
  "name": "marketing-agent-frontend",
  "private": true,
  "scripts": {
    "dev": "next dev -p 3001",
    "build": "next build",
    "start": "next start -p 3001",
    "test": "vitest run"
  },
  "dependencies": {
    "next": "^15.0.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0"
  },
  "devDependencies": {
    "typescript": "^5.5.0",
    "@types/react": "^19.0.0",
    "@types/node": "^22.0.0",
    "vitest": "^2.0.0"
  }
}
EOF
cat > frontend/tsconfig.json << 'EOF'
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["dom", "ES2020"],
    "jsx": "preserve",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "paths": { "@/*": ["./*"] }
  },
  "include": ["**/*.ts", "**/*.tsx"]
}
EOF
cat > frontend/next.config.ts << 'EOF'
import type { NextConfig } from "next";
const nextConfig: NextConfig = {};
export default nextConfig;
EOF
cat > frontend/vitest.config.ts << 'EOF'
import { defineConfig } from "vitest/config";
export default defineConfig({ test: { environment: "node" } });
EOF
```

- [ ] **Step 2: Write api.ts and layout/globals**

```typescript
// frontend/lib/api.ts
const BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8001";

export interface Citation {
  quote: string;
  source_id: string;
}

export interface DiagnosisItem {
  id: string;
  channel: string;
  summary: string;
  kind: "strength" | "weakness";
  citations: Citation[];
  status: "confirmed" | "needs_review" | "unfounded";
}

export interface OpportunityRiskItem {
  id: string;
  kind: "opportunity" | "risk";
  title: string;
  rationale: string;
  citations: Citation[];
  additionally_flagged: boolean;
}

export interface CriticalPoint {
  id: string;
  title: string;
  impact: string;
  urgency: string;
  decision_needed: string;
  citations: Citation[];
}

export interface TimelineLink {
  item_title: string;
  prior_cycle_id: string;
  same_issue: boolean;
  rebuttal_passed: boolean;
  repeat_count: number;
}

export interface ActionItem {
  id: string;
  title: string;
  owner: string;
  due: string;
  priority: "high" | "mid" | "low";
  source_item_ids: string[];
}

export interface CycleReport {
  cycle_id: string;
  diagnosis: DiagnosisItem[];
  opportunities_risks: OpportunityRiskItem[];
  critical_points: CriticalPoint[];
  timeline: TimelineLink[];
  action_items: ActionItem[];
  overview: string;
  overview_warnings: string[];
  coverage_note: string;
}

export async function addSource(cycleId: string, title: string, text: string): Promise<{ id: string }> {
  const res = await fetch(`${BASE}/sources`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ cycle_id: cycleId, title, text }),
  });
  if (!res.ok) throw new Error(`업로드 실패: ${res.status}`);
  return res.json();
}

export async function runPipeline(cycleId: string): Promise<CycleReport> {
  const res = await fetch(`${BASE}/pipeline/run?cycle_id=${encodeURIComponent(cycleId)}`, { method: "POST" });
  if (!res.ok) throw new Error(`파이프라인 실행 실패: ${res.status}`);
  return res.json();
}

export async function getReport(cycleId: string): Promise<CycleReport | null> {
  const res = await fetch(`${BASE}/reports/${encodeURIComponent(cycleId)}`);
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`리포트 조회 실패: ${res.status}`);
  return res.json();
}

export async function listCycles(): Promise<string[]> {
  const res = await fetch(`${BASE}/cycles`);
  if (!res.ok) throw new Error(`회차 목록 조회 실패: ${res.status}`);
  return res.json();
}
```

```tsx
// frontend/app/layout.tsx
import "./globals.css";
import type { ReactNode } from "react";

export const metadata = { title: "marketing-agent" };

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
```

```css
/* frontend/app/globals.css */
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: -apple-system, "Malgun Gothic", sans-serif;
  background: #0b0d12;
  color: #e6e8eb;
}
a { color: inherit; }
```

- [ ] **Step 3: Write failing test for api client (using fetch mock)**

```typescript
// frontend/lib/api.test.ts
import { describe, it, expect, vi, beforeEach } from "vitest";
import { addSource, runPipeline, getReport, listCycles } from "./api";

beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn());
});

describe("api client", () => {
  it("addSource posts cycle_id/title/text and returns id", async () => {
    (fetch as any).mockResolvedValue({ ok: true, json: async () => ({ id: "s-1" }) });
    const result = await addSource("c1", "이메일", "본문");
    expect(result.id).toBe("s-1");
    const [url, opts] = (fetch as any).mock.calls[0];
    expect(url).toContain("/sources");
    expect(JSON.parse(opts.body)).toEqual({ cycle_id: "c1", title: "이메일", text: "본문" });
  });

  it("runPipeline posts to /pipeline/run with cycle_id query param", async () => {
    (fetch as any).mockResolvedValue({ ok: true, json: async () => ({ cycle_id: "c1" }) });
    await runPipeline("c1");
    const [url, opts] = (fetch as any).mock.calls[0];
    expect(url).toContain("/pipeline/run?cycle_id=c1");
    expect(opts.method).toBe("POST");
  });

  it("getReport returns null on 404", async () => {
    (fetch as any).mockResolvedValue({ ok: false, status: 404 });
    const result = await getReport("missing");
    expect(result).toBeNull();
  });

  it("listCycles returns array from response", async () => {
    (fetch as any).mockResolvedValue({ ok: true, json: async () => ["c1", "c2"] });
    const result = await listCycles();
    expect(result).toEqual(["c1", "c2"]);
  });
});
```

- [ ] **Step 4: Install deps and run tests**

```bash
cd frontend && npm install --silent
npm test
```
Expected: 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/package.json frontend/tsconfig.json frontend/next.config.ts frontend/vitest.config.ts frontend/app/layout.tsx frontend/app/globals.css frontend/lib/api.ts frontend/lib/api.test.ts
git commit -m "feat: frontend scaffolding and typed API client"
```

---

## Task 10: Dashboard UI (upload, run, report view)

**Files:**
- Create: `frontend/app/page.tsx`
- Create: `frontend/components/ReportView.tsx`
- Create: `frontend/components/UploadForm.tsx`

**Interfaces:**
- Consumes: `lib/api.ts` exports from Task 9.
- Produces: `page.tsx` default export (client component) rendering: cycle id input, `UploadForm` (title+text+cycle → `addSource`), "파이프라인 실행" button (→ `runPipeline`), `ReportView` displaying the returned `CycleReport` — diagnosis grouped by strength/weakness with status badges, opportunities/risks list, critical points, timeline links ("N회차째 반복" via `repeat_count`), action items table, overview text + warnings, coverage note.

- [ ] **Step 1: Write UploadForm.tsx**

```tsx
// frontend/components/UploadForm.tsx
"use client";
import { useState } from "react";
import { addSource } from "@/lib/api";

export function UploadForm({ cycleId, onUploaded }: { cycleId: string; onUploaded: () => void }) {
  const [title, setTitle] = useState("");
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit() {
    if (!title.trim() || !text.trim()) {
      setError("제목과 본문을 입력하세요.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      await addSource(cycleId, title, text);
      setTitle("");
      setText("");
      onUploaded();
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8, maxWidth: 480 }}>
      <input placeholder="자료 제목 (예: 8월 이메일 캠페인)" value={title} onChange={(e) => setTitle(e.target.value)} />
      <textarea placeholder="본문 붙여넣기" rows={6} value={text} onChange={(e) => setText(e.target.value)} />
      {error && <p style={{ color: "#f66" }}>{error}</p>}
      <button onClick={submit} disabled={busy}>{busy ? "업로드 중..." : "자료 추가"}</button>
    </div>
  );
}
```

- [ ] **Step 2: Write ReportView.tsx**

```tsx
// frontend/components/ReportView.tsx
import type { CycleReport } from "@/lib/api";

export function ReportView({ report }: { report: CycleReport }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      <section>
        <h2>총평</h2>
        <p>{report.overview}</p>
        {report.overview_warnings.length > 0 && (
          <ul style={{ color: "#f0b429" }}>
            {report.overview_warnings.map((w, i) => <li key={i}>근거 미확인: {w}</li>)}
          </ul>
        )}
        <p style={{ opacity: 0.7 }}>{report.coverage_note}</p>
      </section>

      <section>
        <h2>현황진단</h2>
        <ul>
          {report.diagnosis.map((d) => (
            <li key={d.id}>
              [{d.channel}] {d.summary} — {d.kind === "strength" ? "강점" : "약점"}
              {" "}<span style={{ opacity: 0.7 }}>({statusLabel(d.status)})</span>
              {d.citations.length > 0 && (
                <ul>{d.citations.map((c, i) => <li key={i} style={{ opacity: 0.7 }}>&quot;{c.quote}&quot;</li>)}</ul>
              )}
            </li>
          ))}
        </ul>
      </section>

      <section>
        <h2>기회 / 리스크</h2>
        <ul>
          {report.opportunities_risks.map((o) => (
            <li key={o.id}>
              [{o.kind === "opportunity" ? "기회" : "리스크"}] {o.title} — {o.rationale}
              {o.additionally_flagged && <span> (추가 지적 항목)</span>}
            </li>
          ))}
        </ul>
      </section>

      <section>
        <h2>Critical Point</h2>
        <ul>
          {report.critical_points.map((cp) => (
            <li key={cp.id}>{cp.title} — 임팩트: {cp.impact}, 시급성: {cp.urgency}, 필요 결정: {cp.decision_needed}</li>
          ))}
        </ul>
      </section>

      <section>
        <h2>타임라인</h2>
        <ul>
          {report.timeline.map((t, i) => (
            <li key={i}>{t.item_title} — {t.prior_cycle_id} 회차부터 이어짐 ({t.repeat_count}회차째 반복)</li>
          ))}
        </ul>
      </section>

      <section>
        <h2>Action Items</h2>
        <table>
          <thead><tr><th>항목</th><th>담당</th><th>기한</th><th>우선순위</th></tr></thead>
          <tbody>
            {report.action_items.map((a) => (
              <tr key={a.id}><td>{a.title}</td><td>{a.owner}</td><td>{a.due}</td><td>{a.priority}</td></tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}

function statusLabel(status: string): string {
  if (status === "confirmed") return "확정";
  if (status === "unfounded") return "근거 미확인";
  return "확인 필요";
}
```

- [ ] **Step 3: Write page.tsx**

```tsx
// frontend/app/page.tsx
"use client";
import { useState } from "react";
import { runPipeline, getReport, type CycleReport } from "@/lib/api";
import { UploadForm } from "@/components/UploadForm";
import { ReportView } from "@/components/ReportView";

export default function Home() {
  const [cycleId, setCycleId] = useState("2026-W32");
  const [report, setReport] = useState<CycleReport | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function handleRun() {
    setBusy(true);
    setError("");
    try {
      const result = await runPipeline(cycleId);
      setReport(result);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  async function handleLoadExisting() {
    setError("");
    try {
      const result = await getReport(cycleId);
      setReport(result);
      if (!result) setError("이 회차의 리포트가 아직 없습니다.");
    } catch (e) {
      setError(String(e));
    }
  }

  return (
    <main style={{ maxWidth: 900, margin: "0 auto", padding: 24 }}>
      <h1>marketing-agent</h1>
      <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 16 }}>
        <label>회차: <input value={cycleId} onChange={(e) => setCycleId(e.target.value)} /></label>
        <button onClick={handleLoadExisting}>불러오기</button>
        <button onClick={handleRun} disabled={busy}>{busy ? "실행 중..." : "파이프라인 실행"}</button>
      </div>

      <UploadForm cycleId={cycleId} onUploaded={() => {}} />

      {error && <p style={{ color: "#f66" }}>{error}</p>}
      {report && <div style={{ marginTop: 24 }}><ReportView report={report} /></div>}
    </main>
  );
}
```

- [ ] **Step 4: Type-check the frontend**

```bash
cd frontend && npx tsc --noEmit
```
Expected: no errors (fix any before proceeding)

- [ ] **Step 5: Commit**

```bash
git add frontend/app/page.tsx frontend/components/ReportView.tsx frontend/components/UploadForm.tsx
git commit -m "feat: dashboard UI for upload, pipeline run, and report view"
```

---

## Task 11: Timeline repeat_count wiring + orchestrator test update

**Files:**
- Modify: `backend/app/orchestrator.py`
- Modify: `backend/tests/test_orchestrator.py`

**Interfaces:**
- Consumes: `TimelineLink` from Task 1, prior reports from `Store`.
- Produces: updated `run_pipeline` sets `repeat_count` on each `TimelineLink` by counting how many consecutive prior cycles already had a link with the same `item_title` (via each prior `CycleReport.timeline`), so the frontend's "N회차째 반복" is accurate instead of always 1.

- [ ] **Step 1: Add failing test for repeat_count**

```python
# append to backend/tests/test_orchestrator.py
@pytest.mark.asyncio
async def test_run_pipeline_computes_repeat_count():
    store = make_store()
    store.add_source(SourceDoc(id="s0", cycle_id="c0", title="t", text="오픈율이 하락했다."))
    store.add_source(SourceDoc(id="s1", cycle_id="c1", title="t", text="오픈율이 하락했다."))

    base_responses = {
        "d1": {"items": [{"channel": "이메일", "summary": "오픈율 하락", "kind": "weakness", "citations": []}]},
        "d2": {"items": []}, "d3": {"items": []}, "v": {"items": []}, "v2": {"items": []},
        "actions": {"items": []}, "overview": "총평.", "v3-check": {"unsupported_sentences": []},
    }
    client0 = StubChatClient({**base_responses, "t1-match": {"matches": []}})
    await run_pipeline(client0, store, "c0")

    client1 = StubChatClient({
        **base_responses,
        "t1-match": {"matches": [{"current": "오픈율 하락", "prior_cycle": "c0", "prior_title": "오픈율 하락"}]},
        "t1-rebut": {"same_issue": True},
    })
    report1 = await run_pipeline(client1, store, "c1")

    assert report1.timeline[0].repeat_count == 2
```

- [ ] **Step 2: Run to verify fail**

```bash
cd backend && .venv/bin/pytest tests/test_orchestrator.py -v -k repeat_count
```
Expected: FAIL (repeat_count defaults to 1, test expects 2)

- [ ] **Step 3: Implement repeat_count computation in orchestrator.py**

Add a helper and use it after computing `timeline`:

```python
def _compute_repeat_count(link, prior_cycle_ids: list[str], store: Store) -> int:
    count = 1
    for pc in reversed(prior_cycle_ids):
        prior_report = store.get_report(pc)
        if prior_report and any(t.item_title == link.item_title for t in prior_report.timeline):
            count += 1
        if prior_report and pc == link.prior_cycle_id:
            break
    return count
```

In `run_pipeline`, after `timeline = await run_t1(...)`, replace with:

```python
    raw_timeline = await run_t1(client, cycle_id, current_titles, prior_titles)
    timeline = [
        t.model_copy(update={"repeat_count": _compute_repeat_count(t, prior_cycle_ids, store)})
        for t in raw_timeline
    ]
```

- [ ] **Step 4: Run tests to verify pass**

```bash
cd backend && .venv/bin/pytest tests/test_orchestrator.py -v
```
Expected: all PASS

- [ ] **Step 5: Run full backend suite**

```bash
cd backend && .venv/bin/pytest -v
```
Expected: all PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/orchestrator.py backend/tests/test_orchestrator.py
git commit -m "feat: compute timeline repeat_count across cycles"
```

---

## Task 12: README, env examples, run scripts

**Files:**
- Create: `README.md`
- Create: `backend/.env.example`
- Create: `scripts/setup.sh`
- Create: `.gitignore`

**Interfaces:**
- Produces: developer-facing docs; no code interfaces.

- [ ] **Step 1: Write .gitignore**

```bash
cat > .gitignore << 'EOF'
backend/.venv/
backend/data/*.db
backend/__pycache__/
backend/**/__pycache__/
backend/.pytest_cache/
frontend/node_modules/
frontend/.next/
frontend/*.tsbuildinfo
.DS_Store
EOF
```

- [ ] **Step 2: Write backend/.env.example**

```bash
mkdir -p backend
cat > backend/.env.example << 'EOF'
MA_DB_PATH=data/marketing_agent.db
MA_LLM_BASE_URL=http://localhost:8700/v1
MA_LLM_API_KEY=changeme
MA_LLM_MODEL=marketing-agent
EOF
```

- [ ] **Step 3: Write scripts/setup.sh**

```bash
mkdir -p scripts
cat > scripts/setup.sh << 'EOF'
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== backend =="
cd backend
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]" -q
[ -f .env ] || cp .env.example .env
cd ..

echo "== frontend =="
cd frontend
npm install --silent
cd ..

echo "설정 완료. 실행:"
echo "  backend:  cd backend && .venv/bin/uvicorn app.main:app --reload --port 8001"
echo "  frontend: cd frontend && npm run dev"
EOF
chmod +x scripts/setup.sh
```

- [ ] **Step 4: Write README.md**

```markdown
# marketing-agent

영업/마케팅 현황진단·타임라인·Action Items를 생성하는 multi-agent 하네스.
`weekly-report-harness`의 아키텍처(독립 재도출 검증, 축자 인용 그라운딩, 반박
검증 기반 타임라인 연속성)를 영업/마케팅 도메인에 적용했다. 설계 배경은
`docs/superpowers/specs/2026-08-11-marketing-agent-design.md` 참고.

## 빠른 시작

\`\`\`sh
scripts/setup.sh
cd backend && .venv/bin/uvicorn app.main:app --reload --port 8001 &
cd frontend && npm run dev
\`\`\`

화면: http://localhost:3001 · API: http://localhost:8001/docs

## 아키텍처

원문 업로드 → 정규화 → 병렬 진단(D1 현황진단 ∥ D2 기회·리스크 ∥ D3 Critical
Point ∥ V·V2 독립 교차검증) → 타임라인 연속성(T1, 반박 검증) → Action Items +
총평(V3 사실검증) → 리포트.

에이전트 그래프는 `backend/app/orchestrator.py`의 `AGENT_CATALOG`에 `needs`로
선언되어 있고, 실행이 그 선언을 지키는지 `backend/tests/test_orchestrator.py`가
검사한다.

## 테스트

\`\`\`sh
cd backend && .venv/bin/pytest -v
cd frontend && npm test
\`\`\`

모든 에이전트/파이프라인 테스트는 실제 LLM 호출 없이 `StubChatClient`로
동작한다 — 실 LLM 연동은 `MA_LLM_BASE_URL`(hermes-gateway 등 OpenAI 호환
엔드포인트)로 `backend/.env`에서 설정한다.
```

- [ ] **Step 5: Commit**

```bash
git add README.md backend/.env.example scripts/setup.sh .gitignore
git commit -m "docs: README, env example, and setup script"
```

---

## Task 13: Full-suite verification

**Files:** none (verification only)

- [ ] **Step 1: Run backend suite fresh**

```bash
cd backend && .venv/bin/pytest -v
```
Expected: all tests PASS, 0 failures

- [ ] **Step 2: Run frontend suite fresh**

```bash
cd frontend && npm test
```
Expected: all tests PASS

- [ ] **Step 3: Type-check frontend**

```bash
cd frontend && npx tsc --noEmit
```
Expected: no errors

- [ ] **Step 4: Boot both servers and smoke-test manually with curl**

```bash
cd backend && MA_LLM_BASE_URL=http://localhost:9/no-such-host .venv/bin/uvicorn app.main:app --port 8001 &
sleep 2
curl -s http://localhost:8001/health
curl -s -X POST http://localhost:8001/sources -H 'Content-Type: application/json' \
  -d '{"cycle_id":"smoke","title":"t","text":"오픈율이 하락했다."}'
curl -s http://localhost:8001/cycles
kill %1
```
Expected: `/health` returns `{"status":"ok"}`, `/sources` returns an id, `/cycles` returns `[]` (pipeline not run since no live LLM here — this step only proves the server boots and non-LLM routes work)

- [ ] **Step 5: Commit final state if anything changed**

```bash
git status
# if changes exist:
git add -A && git commit -m "chore: final verification pass"
```
