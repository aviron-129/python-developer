import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient

from outbox.main import create_app


def client():
    return TestClient(create_app(":memory:"))


def test_order_writes_outbox_but_not_invoice():
    api = client()
    created = api.post("/orders", json={"customer": "nina", "sku": "mug", "total": 42000})
    assert created.status_code == 201
    assert api.get("/billing/invoices").json() == []
    pending = api.get("/outbox").json()
    assert len(pending) == 1
    assert pending[0]["event_type"] == "order.placed"
    assert pending[0]["payload"]["customer"] == "nina"


def test_relay_is_idempotent():
    api = client()
    api.post("/orders", json={"customer": "nina", "sku": "mug", "total": 42000})
    first = api.post("/relay/tick")
    second = api.post("/relay/tick")
    assert first.status_code == 200
    assert len(first.json()["delivered"]) == 1
    assert second.json()["delivered"] == []
    assert len(api.get("/billing/invoices").json()) == 1
    assert api.get("/outbox").json() == []


def test_direct_consume_twice_keeps_one_invoice():
    api = client()
    body = {
        "message_id": "msg-1",
        "event_type": "order.placed",
        "payload": {"order_id": "ord-1", "total": 1000},
    }
    assert api.post("/billing/consume", json=body).json()["status"] == "accepted"
    again = api.post("/billing/consume", json=body).json()
    assert again["status"] == "duplicate"
    assert len(again["invoices"]) == 1
