import tempfile, os
from app.storage import Store
from app.demo_fixture import seed_demo_data, DEMO_CYCLE_ID
from app.schemas import CycleReport


def make_store():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    return Store(path)


def test_seed_demo_data_populates_empty_store():
    store = make_store()
    seed_demo_data(store)
    assert store.list_cycles() == [DEMO_CYCLE_ID]
    report = store.get_report(DEMO_CYCLE_ID)
    assert report is not None
    assert isinstance(report, CycleReport)
    assert len(report.diagnosis) > 0
    assert len(report.strategy_timeline.strategic_axes) == 3
    assert report.action_items.immediate_check


def test_seed_demo_data_skips_when_store_not_empty():
    store = make_store()
    store.save_report(CycleReport(cycle_id="real-2026-W40"))
    seed_demo_data(store)
    assert store.list_cycles() == ["real-2026-W40"]
