import pytest
from app.schemas import DiagnosisItem, OpportunityRiskItem, CriticalPoint
from app.agents_actions import run_action_items, run_overview
from tests.stub_client import StubChatClient

DIAG = [DiagnosisItem(id="d1", channel="이메일", summary="오픈율 하락", kind="weakness")]
OPP = [OpportunityRiskItem(id="o1", kind="risk", title="구독 해지 증가", rationale="r")]
CP: list[CriticalPoint] = []


@pytest.mark.asyncio
async def test_run_action_items_orders_immediate_then_needed_then_summary():
    client = StubChatClient({
        "actions": {
            "immediate_check": [
                {"title": "오픈율 급락 원인 긴급 점검", "owner": "마케팅팀", "due": "2026-08-12",
                 "priority": "high", "impact": "high", "effort": "low", "source_item_ids": ["d1"]}
            ],
            "action_needed": [
                {"title": "이메일 제목 A/B 테스트 실시", "owner": "마케팅팀", "due": "2026-08-25",
                 "priority": "mid", "impact": "mid", "effort": "high", "source_item_ids": ["d1"]}
            ],
            "final_summary": "오픈율 하락이 시급하며, 나머지는 순차 대응한다.",
        }
    })
    report = await run_action_items(client, DIAG, OPP, CP)
    assert len(report.immediate_check) == 1
    assert report.immediate_check[0].owner == "마케팅팀"
    assert report.immediate_check[0].source_item_ids == ["d1"]
    assert report.immediate_check[0].impact == "high"
    assert report.immediate_check[0].effort == "low"
    assert len(report.action_needed) == 1
    assert report.final_summary == "오픈율 하락이 시급하며, 나머지는 순차 대응한다."


@pytest.mark.asyncio
async def test_run_action_items_defaults_impact_effort_when_missing():
    client = StubChatClient({
        "actions": {
            "immediate_check": [
                {"title": "긴급 항목", "owner": "팀", "due": "2026-08-12", "priority": "high",
                 "source_item_ids": []}
            ],
            "action_needed": [],
            "final_summary": "",
        }
    })
    report = await run_action_items(client, DIAG, OPP, CP)
    assert report.immediate_check[0].impact == "mid"
    assert report.immediate_check[0].effort == "mid"


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
