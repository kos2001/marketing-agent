import tempfile, os
from app.storage import Store
from app.schemas import SourceDoc, CycleReport, DiagnosisItem


def make_store():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    return Store(path)


def test_add_and_fetch_sources():
    store = make_store()
    store.add_source(SourceDoc(id="s1", cycle_id="2026-W32", title="이메일 성과", text="오픈율 12%"))
    docs = store.sources_for_cycle("2026-W32")
    assert len(docs) == 1
    assert docs[0].text == "오픈율 12%"
    assert docs[0].source_type == "manual"


def test_add_source_preserves_source_type():
    store = make_store()
    store.add_source(SourceDoc(id="s1", cycle_id="2026-W32", title="CRM 내보내기",
                                text="파이프라인 현황", source_type="crm"))
    docs = store.sources_for_cycle("2026-W32")
    assert docs[0].source_type == "crm"


def test_save_and_get_report_roundtrip():
    store = make_store()
    report = CycleReport(
        cycle_id="2026-W32",
        diagnosis=[DiagnosisItem(id="d1", channel="이메일", summary="하락", kind="weakness")],
    )
    store.save_report(report)
    fetched = store.get_report("2026-W32")
    assert fetched is not None
    assert fetched.diagnosis[0].summary == "하락"


def test_prior_cycles_chronological():
    store = make_store()
    for cid in ["2026-W30", "2026-W31", "2026-W32"]:
        store.save_report(CycleReport(cycle_id=cid))
    assert store.prior_cycles("2026-W32") == ["2026-W30", "2026-W31"]


def test_bm25_search_finds_matching_source():
    store = make_store()
    store.add_source(SourceDoc(id="s1", cycle_id="c1", title="이메일 성과", text="오픈율이 12%에서 8%로 하락했다."))
    store.add_source(SourceDoc(id="s2", cycle_id="c1", title="CRM 파이프라인", text="신규 계약 3건이 성사되었다."))

    results = store.bm25_search("오픈율 하락")
    assert [r[0] for r in results] == ["s1"]


def test_bm25_search_scoped_to_cycle():
    store = make_store()
    store.add_source(SourceDoc(id="s1", cycle_id="c1", title="이메일", text="오픈율이 하락했다."))
    store.add_source(SourceDoc(id="s2", cycle_id="c2", title="이메일", text="오픈율이 하락했다."))

    results = store.bm25_search("오픈율", cycle_id="c1")
    assert [r[0] for r in results] == ["s1"]


def test_bm25_search_no_match_returns_empty():
    store = make_store()
    store.add_source(SourceDoc(id="s1", cycle_id="c1", title="이메일", text="오픈율이 하락했다."))
    assert store.bm25_search("존재하지않는단어xyz") == []


def test_bm25_search_updates_after_re_add():
    store = make_store()
    store.add_source(SourceDoc(id="s1", cycle_id="c1", title="이메일", text="오픈율이 하락했다."))
    store.add_source(SourceDoc(id="s1", cycle_id="c1", title="이메일(수정)", text="완전히 다른 내용이다."))

    assert store.bm25_search("오픈율") == []
    results = store.bm25_search("완전히 다른")
    assert [r[0] for r in results] == ["s1"]


def test_embedding_roundtrip():
    store = make_store()
    store.set_embedding("s1", b"\x00\x01\x02\x03")
    assert store.get_embedding("s1") == b"\x00\x01\x02\x03"
    assert store.get_embedding("nope") is None
