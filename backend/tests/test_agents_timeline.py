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
