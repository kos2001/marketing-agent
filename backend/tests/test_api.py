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
    "actions": {"items": []},
    "overview": "총평.",
    "v3-check": {"unsupported_sentences": []},
}


@pytest.fixture
def client():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    test_store = Store(path)
    app.dependency_overrides[get_store] = lambda: test_store
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
