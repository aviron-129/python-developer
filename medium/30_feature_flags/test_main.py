import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient

from flags.main import create_app


def test_allowlist_beats_zero_percent_and_user_is_sticky():
    client = TestClient(create_app(":memory:"))
    client.put("/flags/checkout_v2", json={"name": "checkout_v2", "percent": 0, "allow_tenants": ["alpha"]})
    blocked = client.post("/flags/checkout_v2/evaluate", json={"user_id": "ada", "tenant": "beta"})
    allowed = client.post("/flags/checkout_v2/evaluate", json={"user_id": "ada", "tenant": "alpha"})
    assert blocked.json()["enabled"] is False
    assert allowed.json()["reason"] == "allowlist"
    client.put("/flags/checkout_v2", json={"name": "checkout_v2", "percent": 100, "allow_tenants": []})
    first = client.post("/flags/checkout_v2/evaluate", json={"user_id": "ada", "tenant": "beta"}).json()
    second = client.post("/flags/checkout_v2/evaluate", json={"user_id": "ada", "tenant": "beta"}).json()
    assert first["enabled"] is True
    assert first["bucket"] == second["bucket"]
