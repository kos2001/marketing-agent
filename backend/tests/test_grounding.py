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
