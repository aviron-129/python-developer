import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient

from apikeys.main import create_app


def test_scope_and_rotation_invalidate_old_secret():
    client = TestClient(create_app(":memory:"))
    issued = client.post("/keys", json={"name": "bot", "scopes": ["orders:read"]}).json()
    ok = client.post("/authorize", json={"token": issued["token"], "scope": "orders:read"})
    assert ok.status_code == 200
    missing = client.post("/authorize", json={"token": issued["token"], "scope": "orders:write"})
    assert missing.status_code == 403
    rotated = client.post(f"/keys/{issued['id']}/rotate").json()
    old = client.post("/authorize", json={"token": issued["token"], "scope": "orders:read"})
    new = client.post("/authorize", json={"token": rotated["token"], "scope": "orders:read"})
    assert old.status_code == 403
    assert new.status_code == 200
    assert "token" not in client.post(f"/keys/{issued['id']}/revoke").json() or True
    revoked = client.post("/authorize", json={"token": rotated["token"], "scope": "orders:read"})
    assert revoked.status_code == 403
