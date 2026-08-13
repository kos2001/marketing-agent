import pytest
from fastapi.testclient import TestClient
import tempfile, os

from app.main import app, get_client, get_store
from app.storage import Store
from tests.stub_client import StubChatClient

RESPONSES = {
    "d1": {"items": [{"channel": "이메일", "summary": "오픈율 하락", "kind": "weakness", "citations": []}]},
    "d2": {"items": []},
    "d3": {"items": []},
    "v": {"items": []},
    "v2": {"items": []},
    "t1-match": {"matches": []},
    "summary": {"executive_summary": "요약.", "customer_strategies": [], "corporate_response_process": []},
    "strategy": {
        "issue_guides": [],
        "strategic_axes": [
            {"title": "A", "description": "d", "citations": []},
            {"title": "B", "description": "d", "citations": []},
            {"title": "C", "description": "d", "citations": []},
        ],
        "recommended_timeline": [],
    },
    "actions": {"immediate_check": [], "action_needed": [], "final_summary": ""},
    "overview": "총평.",
    "v3-check": {"unsupported_sentences": []},
}


@pytest.fixture
def store():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    return Store(path)


@pytest.fixture
def client(store):
    app.dependency_overrides[get_store] = lambda: store
    app.dependency_overrides[get_client] = lambda: StubChatClient(RESPONSES)
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_upload_and_run_pipeline(client):
    resp = client.post("/sources", json={"cycle_id": "c1", "title": "이메일", "text": "오픈율이 하락했다."})
    assert resp.status_code == 200

    run_resp = client.post("/pipeline/run", params={"cycle_id": "c1"})
    assert run_resp.status_code == 200
    body = run_resp.json()
    assert body["cycle_id"] == "c1"
    assert body["diagnosis"][0]["channel"] == "이메일"


def test_get_report_and_list_cycles(client):
    client.post("/sources", json={"cycle_id": "c1", "title": "t", "text": "오픈율이 하락했다."})
    client.post("/pipeline/run", params={"cycle_id": "c1"})

    report = client.get("/reports/c1")
    assert report.status_code == 200

    cycles = client.get("/cycles")
    assert cycles.json() == ["c1"]


def test_get_missing_report_404(client):
    resp = client.get("/reports/nope")
    assert resp.status_code == 404


def test_source_types_lists_diverse_sources(client):
    resp = client.get("/source-types")
    assert resp.status_code == 200
    types = resp.json()
    assert "email" in types
    assert "crm" in types
    assert "social" in types
    assert "customer_feedback" in types


def test_add_source_with_source_type(client, store):
    resp = client.post("/sources", json={"cycle_id": "c1", "title": "CRM 파이프라인", "text": "...", "source_type": "crm"})
    assert resp.status_code == 200
    docs = store.sources_for_cycle("c1")
    assert docs[0].source_type == "crm"


def test_add_source_defaults_to_manual(client, store):
    resp = client.post("/sources", json={"cycle_id": "c1", "title": "메모", "text": "..."})
    assert resp.status_code == 200
    docs = store.sources_for_cycle("c1")
    assert docs[0].source_type == "manual"


def test_get_sources_for_cycle(client):
    client.post("/sources", json={"cycle_id": "c1", "title": "CRM", "text": "...", "source_type": "crm"})
    client.post("/sources", json={"cycle_id": "c1", "title": "이메일", "text": "...", "source_type": "email"})
    client.post("/sources", json={"cycle_id": "c2", "title": "다른 회차", "text": "..."})

    resp = client.get("/sources/c1")
    assert resp.status_code == 200
    docs = resp.json()
    assert len(docs) == 2
    assert {d["source_type"] for d in docs} == {"crm", "email"}


def test_get_sources_for_empty_cycle(client):
    resp = client.get("/sources/nope")
    assert resp.status_code == 200
    assert resp.json() == []
