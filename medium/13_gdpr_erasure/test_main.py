import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient

from privacy.main import create_app


def test_export_contains_profile_then_erasure_removes_it():
    client = TestClient(create_app(":memory:"))
    user = client.post("/users", json={"name": "Нина", "email": "nina@example.com"}).json()
    client.post(f"/users/{user['id']}/orders", json={"title": "Кружка", "total": 900})
    exported = client.post(f"/users/{user['id']}/export")
    assert exported.json()["user"]["email"] == "nina@example.com"
    assert exported.json()["orders"][0]["title"] == "Кружка"
    erased = client.post(f"/users/{user['id']}/erase")
    assert erased.json()["erased"] is True
    assert erased.json()["email"] is None
    later = client.post(f"/users/{user['id']}/export")
    assert later.json()["user"]["name"] is None
    assert later.json()["orders"][0]["total"] == 900
