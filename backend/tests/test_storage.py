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
