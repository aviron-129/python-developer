import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient

from workflow.main import create_app


def test_author_cannot_approve_and_reject_returns_to_draft():
    client = TestClient(create_app(":memory:"))
    doc = client.post("/documents", json={"title": "Договор", "author": "ada"}).json()
    assert client.post(f"/documents/{doc['id']}/publish", json={"actor": "ada"}).status_code == 409
    client.post(f"/documents/{doc['id']}/submit", json={"actor": "ada"})
    own = client.post(f"/documents/{doc['id']}/approve", json={"actor": "ada"})
    assert own.json()["detail"]["code"] == "author_cannot_approve"
    rejected = client.post(f"/documents/{doc['id']}/reject", json={"actor": "boris"})
    assert rejected.json()["status"] == "draft"
    client.post(f"/documents/{doc['id']}/submit", json={"actor": "ada"})
    approved = client.post(f"/documents/{doc['id']}/approve", json={"actor": "boris"})
    published = client.post(f"/documents/{approved.json()['id']}/publish", json={"actor": "boris"})
    assert published.json()["status"] == "published"
