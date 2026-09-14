import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient

from dlq.main import create_app


def test_failures_land_in_dlq_and_replay_succeeds():
    client = TestClient(create_app(":memory:"))
    job = client.post("/jobs", json={"payload": {"fail": True, "succeed_on": 99}}).json()
    client.post("/workers/tick")
    client.post("/workers/tick")
    third = client.post("/workers/tick").json()[0]
    assert third["status"] == "dead"
    assert third["attempts"] == 3
    assert client.get("/dead").json()[0]["id"] == job["id"]
    client.post(f"/dead/{job['id']}/replay")
    done = client.post("/workers/tick").json()[0]
    assert done["status"] == "done"
    assert client.get("/dead").json() == []
