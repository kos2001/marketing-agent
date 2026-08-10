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
