from __future__ import annotations
import uuid
from .llm import ChatClient, extract_json
from .grounding import ground_citations
from .schemas import (
    SourceDoc,
    DiagnosisItem,
    OpportunityRiskItem,
    CriticalPoint,
    Citation,
    CustomerStrategy,
    ProcessStep,
    DiagnosisSummary,
)

SUMMARY_SYSTEM = (
    "당신은 현황진단 종합관입니다. 채널별 현황진단·기회·리스크·Critical Point를 "
    "임원 의사결정 형식으로 재구성하십시오. 세 부분을 만듭니다:\n"
    "1) executive_summary: 3~5문장의 핵심 요약.\n"
    "2) customer_strategies: 원문에서 특정 고객사·거래처·세그먼트가 식별되면 그 "
    "고객별로 situation(현황)과 strategy(대응 방향)를 적으십시오. 원문에 특정 고객이 "
    "전혀 없으면 빈 배열로 두십시오 — 없는 고객을 지어내지 마십시오.\n"
    "3) corporate_response_process: 법인(기업) 고객 대응을 위한 순서 있는 절차. 각 "
    "단계는 order(1부터), title, description, owner(담당 부서/역할, 모르면 빈 문자열)를 "
    "적으십시오. 이 절차는 진단에서 나온 문제를 해결하기 위한 제안이므로 원문 인용을 "
    "요구하지 않습니다.\n\n"
    'JSON 형식: {"executive_summary": str, "customer_strategies": [{"customer": str, '
    '"situation": str, "strategy": str, "citations": [{"quote": str, "source_id": str}]}], '
    '"corporate_response_process": [{"order": int, "title": str, "description": str, '
    '"owner": str}]}. citations의 quote는 원문에서 그대로 축자 인용해야 합니다.'
)


def _sources_text(sources: list[SourceDoc]) -> str:
    return "\n\n".join(f"[{s.id}] {s.title}\n{s.text}" for s in sources)


def _source_map(sources: list[SourceDoc]) -> dict[str, str]:
    return {s.id: s.text for s in sources}


def _input_summary(diag: list[DiagnosisItem], opp: list[OpportunityRiskItem], cp: list[CriticalPoint]) -> str:
    lines = [f"[{i.id}] {i.channel}: {i.summary} ({i.kind})" for i in diag]
    lines += [f"[{i.id}] {i.kind}: {i.title} - {i.rationale}" for i in opp]
    lines += [f"[{i.id}] CP: {i.title} - {i.impact}/{i.urgency}" for i in cp]
    return "\n".join(lines)


async def run_summary(
    client: ChatClient,
    sources: list[SourceDoc],
    diagnosis: list[DiagnosisItem],
    opp_risks: list[OpportunityRiskItem],
    critical_points: list[CriticalPoint],
) -> DiagnosisSummary:
    smap = _source_map(sources)
    user = (
        f"원문 자료:\n{_sources_text(sources)}\n\n"
        f"기존 진단 결과:\n{_input_summary(diagnosis, opp_risks, critical_points)}"
    )
    raw = await client.chat(SUMMARY_SYSTEM, user, session_id="summary")
    data = extract_json(raw)

    customers = []
    for it in data.get("customer_strategies", []):
        citations = [Citation(**c) for c in it.get("citations", [])]
        customers.append(CustomerStrategy(
            id=f"cust-{uuid.uuid4().hex[:8]}",
            customer=it["customer"],
            situation=it["situation"],
            strategy=it["strategy"],
            citations=ground_citations(citations, smap),
        ))

    process = [
        ProcessStep(
            order=it["order"],
            title=it["title"],
            description=it["description"],
            owner=it.get("owner", ""),
        )
        for it in sorted(data.get("corporate_response_process", []), key=lambda x: x["order"])
    ]

    return DiagnosisSummary(
        executive_summary=data.get("executive_summary", ""),
        customer_strategies=customers,
        corporate_response_process=process,
    )
