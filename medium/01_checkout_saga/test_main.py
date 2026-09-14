import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient

from checkout.main import create_app


def client():
    return TestClient(create_app(":memory:"))


def test_confirmed_checkout_takes_stock_once():
    api = client()
    api.post("/skus", json={"sku": "mug", "name": "Кружка", "on_hand": 4})
    created = api.post(
        "/checkouts",
        json={"sku": "mug", "qty": 2, "amount": 150000, "card_token": "tok_ok"},
    )
    assert created.status_code == 201
    body = created.json()
    assert body["state"] == "confirmed"
    assert body["steps"] == ["started", "stock_reserved", "payment_captured"]
    assert body["payment_id"].startswith("pay_")
    assert api.get("/skus/mug").json()["on_hand"] == 2


def test_declined_payment_releases_stock():
    api = client()
    api.post("/skus", json={"sku": "mug", "name": "Кружка", "on_hand": 3})
    created = api.post(
        "/checkouts",
        json={"sku": "mug", "qty": 2, "amount": 90000, "card_token": "decline"},
    )
    assert created.status_code == 201
    body = created.json()
    assert body["state"] == "compensated"
    assert body["steps"] == ["started", "stock_reserved", "stock_released"]
    assert body["reason"] == "Платёж отклонён"
    assert api.get("/skus/mug").json()["on_hand"] == 3


def test_second_checkout_cannot_oversell():
    api = client()
    api.post("/skus", json={"sku": "mug", "name": "Кружка", "on_hand": 1})
    first = api.post(
        "/checkouts",
        json={"sku": "mug", "qty": 1, "amount": 100, "card_token": "tok_ok"},
    )
    second = api.post(
        "/checkouts",
        json={"sku": "mug", "qty": 1, "amount": 100, "card_token": "tok_ok"},
    )
    assert first.json()["state"] == "confirmed"
    assert second.status_code == 409
    assert second.json()["detail"]["code"] == "out_of_stock"
    assert api.get("/skus/mug").json()["on_hand"] == 0
