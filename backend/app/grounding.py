from __future__ import annotations
from .schemas import Citation


def ground_citations(citations: list[Citation], sources: dict[str, str]) -> list[Citation]:
    """원문과 축자 대조해 실재하지 않는 인용을 인용 단위로 제거한다."""
    kept: list[Citation] = []
    for c in citations:
        text = sources.get(c.source_id)
        if text and c.quote.strip() and c.quote in text:
            kept.append(c)
    return kept
