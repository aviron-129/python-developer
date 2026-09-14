import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient

from cdc.main import create_app


def test_view_stays_behind_until_projected():
    client = TestClient(create_app(":memory:"))
    order = client.post("/orders", json={"sku": "mug", "total": 100}).json()
    assert client.get("/views/orders").json() == []
    assert client.post("/project").json()["applied"] == 1
    assert client.get("/views/orders").json()[0]["total"] == 100
    client.patch(f"/orders/{order['id']}", json={"total": 250})
    client.post("/project")
    assert client.get("/views/orders").json()[0]["total"] == 250
    client.delete(f"/orders/{order['id']}")
    client.post("/project")
    assert client.get("/views/orders").json() == []
