import pytest
from app.schemas import SourceDoc, DiagnosisItem, OpportunityRiskItem, CriticalPoint
from app.agents_summary import run_summary
from tests.stub_client import StubChatClient

SOURCES = [SourceDoc(id="s1", cycle_id="c1", title="이메일", text="ACME 법인 담당자가 오픈율 하락에 항의했다.")]
DIAG = [DiagnosisItem(id="d1", channel="이메일", summary="오픈율 하락", kind="weakness")]
OPP: list[OpportunityRiskItem] = []
CP: list[CriticalPoint] = []


@pytest.mark.asyncio
async def test_run_summary_parses_executive_summary_and_grounds_customer_citations():
    client = StubChatClient({
        "summary": {
            "executive_summary": "오픈율이 하락했다.",
            "customer_strategies": [
                {"customer": "ACME", "situation": "오픈율 하락에 항의", "strategy": "전담 대응",
                 "citations": [{"quote": "ACME 법인 담당자가 오픈율 하락에 항의했다", "source_id": "s1"},
                                {"quote": "지어낸 문장", "source_id": "s1"}]}
            ],
            "corporate_response_process": [
                {"order": 2, "title": "재발 방지", "description": "원인 분석 결과 반영", "owner": ""},
                {"order": 1, "title": "즉시 회신", "description": "24시간 내 회신", "owner": "CS팀"},
            ],
        }
    })
    summary = await run_summary(client, SOURCES, DIAG, OPP, CP)
    assert summary.executive_summary == "오픈율이 하락했다."
    assert len(summary.customer_strategies) == 1
    assert len(summary.customer_strategies[0].citations) == 1  # 지어낸 인용 제거됨
    assert [p.order for p in summary.corporate_response_process] == [1, 2]
    assert summary.corporate_response_process[0].owner == "CS팀"


@pytest.mark.asyncio
async def test_run_summary_empty_customers_when_none_in_source():
    client = StubChatClient({
        "summary": {
            "executive_summary": "요약.",
            "customer_strategies": [],
            "corporate_response_process": [],
        }
    })
    summary = await run_summary(client, SOURCES, DIAG, OPP, CP)
    assert summary.customer_strategies == []
    assert summary.corporate_response_process == []
