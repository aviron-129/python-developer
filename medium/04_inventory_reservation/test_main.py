import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient

from inventory.main import create_app


def client():
    return TestClient(create_app(":memory:"))


def test_reserve_then_commit_removes_physical_stock():
    api = client()
    api.post("/items", json={"sku": "mug", "name": "Кружка", "on_hand": 5})
    held = api.post("/reservations", json={"sku": "mug", "qty": 2, "order_ref": "o-1"})
    assert held.status_code == 201
    assert held.json()["status"] == "held"
    item = api.get("/items/mug").json()
    assert item["available"] == 3
    assert item["on_hand"] == 5
    done = api.post(f"/reservations/{held.json()['id']}/commit")
    assert done.json()["status"] == "committed"
    after = api.get("/items/mug").json()
    assert after["on_hand"] == 3
    assert after["reserved"] == 0
    assert after["available"] == 3


def test_second_reserve_cannot_exceed_available():
    api = client()
    api.post("/items", json={"sku": "mug", "name": "Кружка", "on_hand": 2})
    first = api.post("/reservations", json={"sku": "mug", "qty": 2, "order_ref": "o-1"})
    second = api.post("/reservations", json={"sku": "mug", "qty": 1, "order_ref": "o-2"})
    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["detail"]["code"] == "insufficient_stock"


def test_release_returns_available_and_commit_is_final():
    api = client()
    api.post("/items", json={"sku": "mug", "name": "Кружка", "on_hand": 4})
    held = api.post("/reservations", json={"sku": "mug", "qty": 3, "order_ref": "o-1"}).json()
    released = api.post(f"/reservations/{held['id']}/release")
    assert released.json()["status"] == "released"
    assert api.get("/items/mug").json()["available"] == 4
    again = api.post(f"/reservations/{held['id']}/commit")
    assert again.status_code == 409
    assert again.json()["detail"]["code"] == "illegal_transition"


def test_receive_requires_matching_version():
    api = client()
    created = api.post("/items", json={"sku": "mug", "name": "Кружка", "on_hand": 1}).json()
    stale = api.post("/items/mug/receive", json={"qty": 4}, headers={"If-Match": "0"})
    assert stale.status_code == 409
    assert stale.json()["detail"]["code"] == "version_conflict"
    fresh = api.post(
        "/items/mug/receive",
        json={"qty": 4},
        headers={"If-Match": str(created["version"])},
    )
    assert fresh.status_code == 200
    assert fresh.json()["on_hand"] == 5
    assert fresh.json()["version"] == created["version"] + 1
