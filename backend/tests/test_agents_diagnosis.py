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
