import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient

from audit.main import create_app


def test_filter_and_append_only():
    client = TestClient(create_app(":memory:"))
    client.post("/events", json={"actor": "ada", "action": "login", "subject": "session", "at": "2026-09-14T10:00:00Z"})
    client.post("/events", json={"actor": "ada", "action": "export", "subject": "user-1", "at": "2026-09-14T10:05:00Z"})
    client.post("/events", json={"actor": "boris", "action": "login", "subject": "session", "at": "2026-09-14T10:06:00Z"})
    found = client.get("/events", params={"actor": "ada", "action": "export"})
    assert [item["action"] for item in found.json()] == ["export"]
    blocked = client.put("/events/anything")
    assert blocked.status_code == 405
    assert client.get("/events/verify").json()["ok"] is True
