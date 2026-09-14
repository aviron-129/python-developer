import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient

from promos.main import create_app


def test_percent_discount_and_referral_credit():
    client = TestClient(create_app(":memory:"))
    client.post(
        "/codes",
        json={
            "code": "nina10",
            "kind": "percent",
            "value": 10,
            "max_uses": 2,
            "expires_on": "2026-12-31",
            "referrer": "nina",
        },
    )
    redeemed = client.post("/codes/nina10/redeem", json={"user_id": "ada", "amount": 1000, "today": "2026-09-14"})
    assert redeemed.json() == {"code": "NINA10", "discount": 100, "payable": 900, "referrer_credit": 100}
    again = client.post("/codes/nina10/redeem", json={"user_id": "ada", "amount": 1000, "today": "2026-09-14"})
    assert again.json()["detail"]["code"] == "already_used"


def test_expired_and_exhausted():
    client = TestClient(create_app(":memory:"))
    client.post(
        "/codes",
        json={"code": "old", "kind": "fixed", "value": 50, "max_uses": 1, "expires_on": "2026-01-01", "referrer": None},
    )
    expired = client.post("/codes/old/redeem", json={"user_id": "ada", "amount": 100, "today": "2026-09-14"})
    assert expired.json()["detail"]["code"] == "expired"
