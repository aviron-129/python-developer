import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient

from sessions.main import create_app


def test_revoke_one_keeps_the_other():
    client = TestClient(create_app(":memory:"))
    phone = client.post("/login", json={"user_id": "ada", "device": "phone"}).json()
    laptop = client.post("/login", json={"user_id": "ada", "device": "laptop"}).json()
    client.post(f"/sessions/{phone['id']}/revoke")
    dead = client.get("/me", headers={"Authorization": f"Bearer {phone['token']}"})
    live = client.get("/me", headers={"Authorization": f"Bearer {laptop['token']}"})
    assert dead.status_code == 401
    assert live.json()["device"] == "laptop"


def test_revoke_all():
    client = TestClient(create_app(":memory:"))
    first = client.post("/login", json={"user_id": "ada", "device": "phone"}).json()
    client.post("/login", json={"user_id": "ada", "device": "laptop"})
    assert client.post("/users/ada/revoke-all").json()["revoked"] == 2
    assert client.get("/me", headers={"Authorization": f"Bearer {first['token']}"}).status_code == 401
