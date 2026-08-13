"""BM25 + 임베딩 벡터 하이브리드 검색.

~/gitspace/mi-report/backend/app/collection.py의 hybrid_search 패턴(BM25 +
dense 임베딩을 RRF로 결합, 임베딩 비활성/실패 시 BM25로 폴백)을 옮겼다.
"""
from __future__ import annotations

from . import embeddings
from .schemas import SearchResult, SourceDoc
from .storage import Store

_RRF_K = 60  # Reciprocal Rank Fusion 상수 — mi-report/일반적으로 쓰는 값


def _snippet(text: str, max_len: int = 200) -> str:
    text = text.strip().replace("\n", " ")
    return text[:max_len] + ("…" if len(text) > max_len else "")


def _rrf_fuse(ranked_lists: list[list[str]]) -> list[str]:
    """여러 순위 목록을 Reciprocal Rank Fusion으로 합친다. 점수 = sum(1/(k+rank))."""
    scores: dict[str, float] = {}
    for ranked in ranked_lists:
        for rank, item_id in enumerate(ranked, start=1):
            scores[item_id] = scores.get(item_id, 0.0) + 1.0 / (_RRF_K + rank)
    return sorted(scores, key=lambda i: scores[i], reverse=True)


def _semantic_search(store: Store, query: str, *, cycle_id: str | None, limit: int) -> list[str]:
    """의미 임베딩 코사인 유사도 검색. 비활성/실패면 빈 목록(호출부가 BM25만 쓴다)."""
    query_vec = embeddings.embed([query])
    if not query_vec:
        return []
    stored = store.all_embeddings(cycle_id=cycle_id)
    if not stored:
        return []
    scored = [
        (source_id, embeddings.cosine_similarity(query_vec[0], embeddings.bytes_to_vector(vec)))
        for source_id, vec in stored
    ]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [source_id for source_id, _ in scored[:limit]]


def hybrid_search(
    store: Store, query: str, *, cycle_id: str | None = None, limit: int = 10
) -> list[SearchResult]:
    """BM25(항상) + 의미 임베딩(활성 시)을 RRF로 합쳐 상위 결과를 반환한다.

    임베딩이 꺼져 있거나 실패해도 항상 BM25 결과로 동작한다 — 검색 기능이
    임베딩 장애로 죽지 않는다(mi-report의 폴백 규약과 동일).
    """
    bm25_pool = store.bm25_search(query, cycle_id=cycle_id, limit=max(limit * 3, 20))
    bm25_ids = [source_id for source_id, _ in bm25_pool]

    if embeddings.enabled():
        semantic_ids = _semantic_search(store, query, cycle_id=cycle_id, limit=max(limit * 3, 20))
        fused_ids = _rrf_fuse([bm25_ids, semantic_ids]) if semantic_ids else bm25_ids
    else:
        fused_ids = bm25_ids

    results: list[SearchResult] = []
    for source_id in fused_ids[:limit]:
        doc = store.get_source(source_id)
        if doc is None:
            continue
        results.append(_to_result(doc))
    return results


def _to_result(doc: SourceDoc) -> SearchResult:
    return SearchResult(
        id=doc.id,
        cycle_id=doc.cycle_id,
        title=doc.title,
        source_type=doc.source_type,
        snippet=_snippet(doc.text),
    )


def index_embedding(store: Store, doc: SourceDoc) -> None:
    """임베딩이 켜져 있으면 문서 하나를 임베딩해 저장한다. 꺼져 있으면 아무 것도 안 한다."""
    if not embeddings.enabled():
        return
    vectors = embeddings.embed([doc.text])
    if not vectors:
        return
    store.set_embedding(doc.id, embeddings.vector_to_bytes(vectors[0]))
