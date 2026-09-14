import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient

from registry.main import create_app


def test_optional_field_is_compatible_removed_required_is_not():
    client = TestClient(create_app(":memory:"))
    first = client.post("/schemas", json={"name": "order.placed", "required": ["id", "total"], "optional": []})
    assert first.json()["version"] == 1
    second = client.post(
        "/schemas",
        json={"name": "order.placed", "required": ["id", "total"], "optional": ["note"]},
    )
    assert second.json()["version"] == 2
    broken = client.post("/schemas", json={"name": "order.placed", "required": ["id"], "optional": []})
    assert broken.status_code == 409
    assert broken.json()["detail"]["code"] == "required_removed"
    ok = client.post("/schemas/order.placed/versions/1/validate", json={"payload": {"id": "a", "total": 1}})
    missing = client.post("/schemas/order.placed/versions/1/validate", json={"payload": {"id": "a"}})
    assert ok.json()["ok"] is True
    assert missing.json()["detail"]["missing"] == ["total"]
