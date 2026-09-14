import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient

from tenants.main import create_app


def test_tenants_do_not_see_each_other():
    client = TestClient(create_app(":memory:"))
    created = client.post("/notes", json={"body": "секрет альфы"}, headers={"X-Tenant": "alpha"})
    assert created.status_code == 201
    assert client.get("/notes", headers={"X-Tenant": "beta"}).json() == []
    hidden = client.get(f"/notes/{created.json()['id']}", headers={"X-Tenant": "beta"})
    assert hidden.status_code == 404
    visible = client.get("/notes", headers={"X-Tenant": "alpha"})
    assert visible.json()[0]["body"] == "секрет альфы"
    assert client.get("/notes").status_code == 400
