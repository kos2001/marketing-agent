import tempfile, os
from app.storage import Store
from app.schemas import SourceDoc
from app import search as search_mod, embeddings


def make_store():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    return Store(path)


def test_hybrid_search_bm25_only_when_embeddings_disabled(monkeypatch):
    monkeypatch.delenv("MA_EMBEDDINGS", raising=False)
    store = make_store()
    store.add_source(SourceDoc(id="s1", cycle_id="c1", title="이메일", text="오픈율이 하락했다."))
    store.add_source(SourceDoc(id="s2", cycle_id="c1", title="CRM", text="신규 계약이 성사되었다."))

    results = search_mod.hybrid_search(store, "오픈율")
    assert [r.id for r in results] == ["s1"]
    assert results[0].source_type == "manual"
    assert "오픈율" in results[0].snippet


def test_hybrid_search_scoped_to_cycle():
    store = make_store()
    store.add_source(SourceDoc(id="s1", cycle_id="c1", title="이메일", text="오픈율이 하락했다."))
    store.add_source(SourceDoc(id="s2", cycle_id="c2", title="이메일", text="오픈율이 하락했다."))

    results = search_mod.hybrid_search(store, "오픈율", cycle_id="c1")
    assert [r.id for r in results] == ["s1"]


def test_hybrid_search_no_match_returns_empty():
    store = make_store()
    store.add_source(SourceDoc(id="s1", cycle_id="c1", title="이메일", text="오픈율이 하락했다."))
    assert search_mod.hybrid_search(store, "존재하지않는단어xyz") == []


def test_index_embedding_noop_when_disabled(monkeypatch):
    monkeypatch.delenv("MA_EMBEDDINGS", raising=False)
    store = make_store()
    doc = SourceDoc(id="s1", cycle_id="c1", title="이메일", text="오픈율이 하락했다.")
    store.add_source(doc)
    search_mod.index_embedding(store, doc)
    assert store.get_embedding("s1") is None


def test_snippet_truncates_long_text():
    long_text = "가" * 300
    snippet = search_mod._snippet(long_text)
    assert len(snippet) == 201  # 200자 + 말줄임표
    assert snippet.endswith("…")


def test_snippet_keeps_short_text_as_is():
    assert search_mod._snippet("짧은 텍스트") == "짧은 텍스트"


def test_rrf_fuse_prioritizes_items_ranked_high_in_both_lists():
    fused = search_mod._rrf_fuse([["a", "b", "c"], ["b", "a", "c"]])
    assert fused[0] in ("a", "b")
    assert set(fused) == {"a", "b", "c"}
