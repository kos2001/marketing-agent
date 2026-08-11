import pytest
from app.orchestrator import AGENT_CATALOG, run_pipeline
from app.storage import Store
from app.schemas import SourceDoc
from tests.stub_client import StubChatClient
import tempfile, os


def make_store():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    return Store(path)


BASE_SUMMARY = {
    "executive_summary": "요약.",
    "customer_strategies": [],
    "corporate_response_process": [],
}
BASE_STRATEGY = {
    "issue_guides": [],
    "strategic_axes": [
        {"title": "A", "description": "d", "citations": []},
        {"title": "B", "description": "d", "citations": []},
        {"title": "C", "description": "d", "citations": []},
    ],
    "recommended_timeline": [],
}
BASE_ACTIONS = {
    "immediate_check": [{"title": "A/B 테스트", "owner": "마케팅팀", "due": "2026-08-25",
                          "priority": "high", "source_item_ids": []}],
    "action_needed": [],
    "final_summary": "요약.",
}


def test_catalog_declares_needs_matching_spec():
    by_id = {a["id"]: a for a in AGENT_CATALOG}
    assert by_id["D1"]["needs"] == ()
    assert by_id["V"]["needs"] == ()
    assert set(by_id["T1"]["needs"]) == {"D1", "V", "D2", "D3"}
    assert set(by_id["SUMMARY"]["needs"]) == {"D1", "D2", "D3"}
    assert set(by_id["STRATEGY"]["needs"]) == {"D1", "D2", "D3", "T1"}
    assert set(by_id["V3"]["needs"]) == {"D1", "D2", "D3", "V", "V2", "T1"}


@pytest.mark.asyncio
async def test_run_pipeline_produces_full_report():
    store = make_store()
    store.add_source(SourceDoc(id="s1", cycle_id="c1", title="이메일", text="오픈율이 12%로 하락했다."))

    responses = {
        "d1": {"items": [{"channel": "이메일", "summary": "오픈율 하락", "kind": "weakness",
                           "citations": [{"quote": "오픈율이 12%로 하락", "source_id": "s1"}]}]},
        "d2": {"items": [{"kind": "risk", "title": "구독 해지 증가", "rationale": "r", "citations": []}]},
        "d3": {"items": []},
        "v": {"items": [{"channel": "이메일", "kind": "weakness", "summary": "재도출"}]},
        "v2": {"items": []},
        "t1-match": {"matches": []},
        "summary": BASE_SUMMARY,
        "strategy": BASE_STRATEGY,
        "actions": BASE_ACTIONS,
        "overview": "총평입니다.",
        "v3-check": {"unsupported_sentences": []},
    }
    client = StubChatClient(responses)
    report = await run_pipeline(client, store, "c1")

    assert report.cycle_id == "c1"
    assert len(report.diagnosis) == 1
    assert report.diagnosis[0].status == "confirmed"
    assert len(report.action_items.immediate_check) == 1
    assert len(report.strategy_timeline.strategic_axes) == 3
    assert report.diagnosis_summary.executive_summary == "요약."
    assert store.get_report("c1") is not None


@pytest.mark.asyncio
async def test_run_pipeline_computes_repeat_count():
    store = make_store()
    store.add_source(SourceDoc(id="s0", cycle_id="c0", title="t", text="오픈율이 하락했다."))
    store.add_source(SourceDoc(id="s1", cycle_id="c1", title="t", text="오픈율이 하락했다."))

    base_responses = {
        "d1": {"items": [{"channel": "이메일", "summary": "오픈율 하락", "kind": "weakness", "citations": []}]},
        "d2": {"items": []}, "d3": {"items": []}, "v": {"items": []}, "v2": {"items": []},
        "summary": BASE_SUMMARY, "strategy": BASE_STRATEGY,
        "actions": {"immediate_check": [], "action_needed": [], "final_summary": ""},
        "overview": "총평.", "v3-check": {"unsupported_sentences": []},
    }
    client0 = StubChatClient({**base_responses, "t1-match": {"matches": []}})
    await run_pipeline(client0, store, "c0")

    client1 = StubChatClient({
        **base_responses,
        "t1-match": {"matches": [{"current": "오픈율 하락", "prior_cycle": "c0", "prior_title": "오픈율 하락"}]},
        "t1-rebut": {"same_issue": True},
    })
    report1 = await run_pipeline(client1, store, "c1")

    assert report1.timeline[0].repeat_count == 2
