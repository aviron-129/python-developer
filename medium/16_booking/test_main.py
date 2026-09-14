import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient

from bookings.main import create_app


def test_overlap_rejected_until_canceled():
    client = TestClient(create_app(":memory:"))
    client.post("/resources", json={"code": "room-1", "name": "Переговорка"})
    first = client.post(
        "/bookings",
        json={"resource": "room-1", "start_at": "2026-09-14T10:00", "end_at": "2026-09-14T11:00", "guest": "Ада"},
    )
    clash = client.post(
        "/bookings",
        json={"resource": "room-1", "start_at": "2026-09-14T10:30", "end_at": "2026-09-14T11:30", "guest": "Берт"},
    )
    assert first.status_code == 201
    assert clash.status_code == 409
    client.post(f"/bookings/{first.json()['id']}/cancel")
    again = client.post(
        "/bookings",
        json={"resource": "room-1", "start_at": "2026-09-14T10:30", "end_at": "2026-09-14T11:30", "guest": "Берт"},
    )
    assert again.status_code == 201
