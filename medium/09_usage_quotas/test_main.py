import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient

from quotas.main import create_app


def test_limit_blocks_and_new_period_resets():
    client = TestClient(create_app(":memory:"))
    account = client.post("/accounts", json={"name": "shop", "monthly_limit": 100}).json()
    ok = client.post(f"/accounts/{account['id']}/usage", json={"units": 80})
    assert ok.json()["remaining"] == 20
    blocked = client.post(f"/accounts/{account['id']}/usage", json={"units": 30})
    assert blocked.status_code == 429
    assert blocked.json()["detail"]["code"] == "quota_exceeded"
    assert client.get(f"/accounts/{account['id']}").json()["used"] == 80
    reset = client.post(f"/accounts/{account['id']}/close-period")
    assert reset.json()["used"] == 0
    assert reset.json()["period"] == 2
    assert client.post(f"/accounts/{account['id']}/usage", json={"units": 30}).status_code == 200
