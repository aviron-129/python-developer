import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient

from traces.main import create_app


def test_child_error_marks_parent():
    client = TestClient(create_app())
    ok = client.post("/orders", json={"sku": "mug", "qty": 1, "stock": 3}).json()
    trace = client.get(f"/traces/{ok['trace_id']}").json()
    assert [span["name"] for span in trace["spans"]] == ["orders.create", "inventory.reserve"]
    assert trace["spans"][1]["parent_id"] == trace["spans"][0]["id"]
    assert ok["reserved"] is True

    failed = client.post("/orders", json={"sku": "mug", "qty": 5, "stock": 1}).json()
    spans = client.get(f"/traces/{failed['trace_id']}").json()["spans"]
    assert spans[0]["status"] == "error"
    assert spans[1]["status"] == "error"
    assert failed["reserved"] is False
