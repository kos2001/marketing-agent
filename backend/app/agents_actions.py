from __future__ import annotations
import uuid
from .llm import ChatClient, extract_json
from .schemas import DiagnosisItem, OpportunityRiskItem, CriticalPoint, TimelineLink, ActionItem, ActionItemsReport

ACTIONS_SYSTEM = (
    "당신은 실행 전환관입니다. 현황진단·기회·리스크·Critical Point를 바탕으로 실행 "
    "가능한 Action Item을 만드십시오. 다음 순서로 세 부분을 구성합니다:\n"
    "1) immediate_check: 지금 즉시 확인·검토해야 하는 긴급 항목.\n"
    "2) action_needed: 조치가 필요하지만 즉각적인 긴급성은 없는 항목.\n"
    "3) final_summary: 전체 Action Item을 한 문단으로 요약하는 최종 요약.\n\n"
    "각 Action Item은 title, owner(담당), due(YYYY-MM-DD), priority(\"high\"|\"mid\"|"
    '"low"), source_item_ids(입력 항목의 id)를 갖습니다.\n\n'
    'JSON 형식: {"immediate_check": [{"title": str, "owner": str, "due": str, '
    '"priority": str, "source_item_ids": [str]}], "action_needed": [{...같은 형식...}], '
    '"final_summary": str}.'
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


def _parse_action_items(items: list[dict]) -> list[ActionItem]:
    return [
        ActionItem(
            id=f"ai-{uuid.uuid4().hex[:8]}",
            title=it["title"],
            owner=it["owner"],
            due=it["due"],
            priority=it["priority"],
            source_item_ids=it.get("source_item_ids", []),
        )
        for it in items
    ]


async def run_action_items(
    client: ChatClient,
    diagnosis: list[DiagnosisItem],
    opp_risks: list[OpportunityRiskItem],
    critical_points: list[CriticalPoint],
) -> ActionItemsReport:
    user = _input_summary(diagnosis, opp_risks, critical_points)
    raw = await client.chat(ACTIONS_SYSTEM, user, session_id="actions")
    data = extract_json(raw)
    return ActionItemsReport(
        immediate_check=_parse_action_items(data.get("immediate_check", [])),
        action_needed=_parse_action_items(data.get("action_needed", [])),
        final_summary=data.get("final_summary", ""),
    )


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
