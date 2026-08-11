import pytest
from app.schemas import SourceDoc, DiagnosisItem, OpportunityRiskItem, CriticalPoint, TimelineLink
from app.agents_strategy import run_strategy
from tests.stub_client import StubChatClient

SOURCES = [SourceDoc(id="s1", cycle_id="c1", title="이메일", text="오픈율이 12%에서 8%로 하락했다.")]
DIAG = [DiagnosisItem(id="d1", channel="이메일", summary="오픈율 하락", kind="weakness")]
OPP: list[OpportunityRiskItem] = []
CP: list[CriticalPoint] = []
TIMELINE = [TimelineLink(item_title="오픈율 하락", prior_cycle_id="c0", same_issue=True, rebuttal_passed=True, repeat_count=2)]


@pytest.mark.asyncio
async def test_run_strategy_parses_all_three_sections():
    client = StubChatClient({
        "strategy": {
            "issue_guides": [
                {"issue_title": "오픈율 하락", "guide": "제목 A/B 테스트를 우선 실시",
                 "source_item_ids": ["d1"],
                 "citations": [{"quote": "오픈율이 12%에서 8%로 하락했다", "source_id": "s1"}]}
            ],
            "strategic_axes": [
                {"title": "콘텐츠 적합성 강화", "description": "설명1", "citations": []},
                {"title": "채널 다각화", "description": "설명2", "citations": []},
                {"title": "고객 유지 강화", "description": "설명3", "citations": []},
            ],
            "recommended_timeline": [
                {"order": 2, "when": "2주차", "action": "A/B 테스트 결과 반영", "owner": "마케팅팀"},
                {"order": 1, "when": "즉시", "action": "원인 분석", "owner": "데이터팀"},
            ],
        }
    })
    result = await run_strategy(client, SOURCES, DIAG, OPP, CP, TIMELINE)

    assert len(result.issue_guides) == 1
    assert result.issue_guides[0].source_item_ids == ["d1"]
    assert len(result.issue_guides[0].citations) == 1

    assert len(result.strategic_axes) == 3

    assert [s.order for s in result.recommended_timeline] == [1, 2]
    assert result.recommended_timeline[0].action == "원인 분석"


@pytest.mark.asyncio
async def test_run_strategy_drops_fabricated_axis_citation():
    client = StubChatClient({
        "strategy": {
            "issue_guides": [],
            "strategic_axes": [
                {"title": "A", "description": "d", "citations": [
                    {"quote": "오픈율이 12%에서 8%로 하락했다", "source_id": "s1"},
                    {"quote": "지어낸 문장", "source_id": "s1"},
                ]},
                {"title": "B", "description": "d", "citations": []},
                {"title": "C", "description": "d", "citations": []},
            ],
            "recommended_timeline": [],
        }
    })
    result = await run_strategy(client, SOURCES, DIAG, OPP, CP, TIMELINE)
    assert len(result.strategic_axes[0].citations) == 1
