from __future__ import annotations
import uuid
from .llm import ChatClient, extract_json
from .grounding import ground_citations
from .schemas import (
    SourceDoc,
    DiagnosisItem,
    OpportunityRiskItem,
    CriticalPoint,
    TimelineLink,
    Citation,
    StrategicAxis,
    IssueStrategyGuide,
    RecommendedTimelineStep,
    StrategyTimeline,
)

STRATEGY_SYSTEM = (
    "당신은 전략/타임라인 수립관입니다. 현황진단·기회·리스크·Critical Point와 "
    "타임라인 연속성(과거 회차부터 이어지는 사안)을 바탕으로 세 부분을 만듭니다:\n"
    "1) issue_guides: 주요 사안 각각에 대한 대응 전략 가이드. issue_title(사안 이름, "
    "입력에 있는 제목을 그대로 쓸 것), guide(구체적으로 무엇을 해야 하는가), "
    "source_item_ids(그 사안의 id), citations(가능하면 원문 축자 인용).\n"
    "2) strategic_axes: 전체 사안을 관통하는 핵심 전략 방향 정확히 3개. 각 항목은 "
    "title(축의 이름), description(무엇을 왜 하는가), citations.\n"
    "3) recommended_timeline: 앞으로 실행을 언제·무엇을·누가 할지 제안하는 순서 있는 "
    "절차. 이미 여러 회차째 반복되는 사안은 더 이른 시점에 배치하십시오. 각 단계는 "
    "order(1부터), when(예: '1주차', '즉시', '2026-08-25'), action, owner(모르면 빈 "
    "문자열).\n\n"
    'JSON 형식: {"issue_guides": [{"issue_title": str, "guide": str, '
    '"source_item_ids": [str], "citations": [{"quote": str, "source_id": str}]}], '
    '"strategic_axes": [{"title": str, "description": str, "citations": [{"quote": str, '
    '"source_id": str}]}], "recommended_timeline": [{"order": int, "when": str, '
    '"action": str, "owner": str}]}. strategic_axes는 정확히 3개여야 합니다. '
    "citations의 quote는 원문에서 그대로 축자 인용해야 합니다."
)


def _sources_text(sources: list[SourceDoc]) -> str:
    return "\n\n".join(f"[{s.id}] ({s.source_type}) {s.title}\n{s.text}" for s in sources)


def _source_map(sources: list[SourceDoc]) -> dict[str, str]:
    return {s.id: s.text for s in sources}


def _issues_text(diag: list[DiagnosisItem], opp: list[OpportunityRiskItem], cp: list[CriticalPoint]) -> str:
    lines = [f"[{i.id}] {i.channel}: {i.summary} ({i.kind})" for i in diag]
    lines += [f"[{i.id}] {i.kind}: {i.title} - {i.rationale}" for i in opp]
    lines += [f"[{i.id}] CP: {i.title} - {i.impact}/{i.urgency}, 결정 필요: {i.decision_needed}" for i in cp]
    return "\n".join(lines)


def _timeline_text(timeline: list[TimelineLink]) -> str:
    return "\n".join(
        f"{t.item_title}: {t.repeat_count}회차째 반복 (직전 {t.prior_cycle_id} 회차부터)"
        for t in timeline
    )


async def run_strategy(
    client: ChatClient,
    sources: list[SourceDoc],
    diagnosis: list[DiagnosisItem],
    opp_risks: list[OpportunityRiskItem],
    critical_points: list[CriticalPoint],
    timeline: list[TimelineLink],
) -> StrategyTimeline:
    smap = _source_map(sources)
    user = (
        f"원문 자료:\n{_sources_text(sources)}\n\n"
        f"사안 목록:\n{_issues_text(diagnosis, opp_risks, critical_points)}\n\n"
        f"타임라인 연속성:\n{_timeline_text(timeline)}"
    )
    raw = await client.chat(STRATEGY_SYSTEM, user, session_id="strategy")
    data = extract_json(raw)

    guides = []
    for it in data.get("issue_guides", []):
        citations = [Citation(**c) for c in it.get("citations", [])]
        guides.append(IssueStrategyGuide(
            id=f"guide-{uuid.uuid4().hex[:8]}",
            issue_title=it["issue_title"],
            guide=it["guide"],
            source_item_ids=it.get("source_item_ids", []),
            citations=ground_citations(citations, smap),
        ))

    axes = []
    for it in data.get("strategic_axes", []):
        citations = [Citation(**c) for c in it.get("citations", [])]
        axes.append(StrategicAxis(
            id=f"axis-{uuid.uuid4().hex[:8]}",
            title=it["title"],
            description=it["description"],
            citations=ground_citations(citations, smap),
        ))

    steps = [
        RecommendedTimelineStep(
            order=it["order"],
            when=it["when"],
            action=it["action"],
            owner=it.get("owner", ""),
        )
        for it in sorted(data.get("recommended_timeline", []), key=lambda x: x["order"])
    ]

    return StrategyTimeline(issue_guides=guides, strategic_axes=axes, recommended_timeline=steps)
