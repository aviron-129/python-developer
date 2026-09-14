import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient

from subs.main import create_app


def api():
    return TestClient(create_app(":memory:"))


def test_trial_then_successful_renewal():
    client = api()
    client.post("/plans", json={"code": "pro", "price": 99000, "trial_days": 7})
    created = client.post("/subscriptions", json={"plan_code": "pro", "card_token": "tok_ok"})
    assert created.json()["status"] == "trialing"
    assert client.post("/billing/run").json() == []
    client.post("/clock", json={"days": 7})
    renewed = client.post("/billing/run").json()
    assert renewed[0]["status"] == "active"
    assert renewed[0]["failures"] == 0


def test_two_declines_cancel():
    client = api()
    client.post("/plans", json={"code": "pro", "price": 99000, "trial_days": 1})
    sub = client.post("/subscriptions", json={"plan_code": "pro", "card_token": "decline"}).json()
    client.post("/clock", json={"days": 1})
    first = client.post("/billing/run").json()[0]
    assert first["status"] == "past_due"
    second = client.post("/billing/run").json()[0]
    assert second["status"] == "canceled"
    assert second["id"] == sub["id"]
