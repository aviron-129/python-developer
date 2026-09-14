import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient

from reports.main import create_app


def test_download_waits_until_ready():
    client = TestClient(create_app(":memory:"))
    report = client.post("/reports", json={"start_on": "2026-09-01", "end_on": "2026-09-14"}).json()
    assert client.get(f"/reports/{report['id']}/download").status_code == 409
    assert client.post(f"/reports/{report['id']}/tick").json()["progress"] == 50
    ready = client.post(f"/reports/{report['id']}/tick").json()
    assert ready["status"] == "ready"
    downloaded = client.get(f"/reports/{report['id']}/download")
    assert downloaded.json()["body"] == "2026-09-01..2026-09-14"


def test_inverted_range_fails_immediately():
    client = TestClient(create_app(":memory:"))
    report = client.post("/reports", json={"start_on": "2026-09-14", "end_on": "2026-09-01"})
    assert report.json()["status"] == "failed"
