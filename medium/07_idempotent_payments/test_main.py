import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient

from payid.main import create_app


def api():
    return TestClient(create_app(":memory:"))


def test_same_key_returns_same_payment():
    client = api()
    headers = {"Idempotency-Key": "order-9"}
    body = {"amount": 1500, "currency": "rub"}
    first = client.post("/payments", json=body, headers=headers)
    second = client.post("/payments", json=body, headers=headers)
    assert first.status_code == 201
    assert second.status_code == 200
    assert second.headers["idempotent-replayed"] == "true"
    assert first.json()["id"] == second.json()["id"]
    assert second.json()["currency"] == "RUB"


def test_same_key_different_body_conflicts():
    client = api()
    headers = {"Idempotency-Key": "order-9"}
    client.post("/payments", json={"amount": 1500, "currency": "RUB"}, headers=headers)
    conflict = client.post("/payments", json={"amount": 2000, "currency": "RUB"}, headers=headers)
    assert conflict.status_code == 409
    assert conflict.json()["detail"]["code"] == "idempotency_conflict"


def test_refund_once():
    client = api()
    created = client.post(
        "/payments",
        json={"amount": 100, "currency": "RUB"},
        headers={"Idempotency-Key": "k1"},
    ).json()
    assert client.post(f"/payments/{created['id']}/refund").json()["status"] == "refunded"
    again = client.post(f"/payments/{created['id']}/refund")
    assert again.status_code == 409
