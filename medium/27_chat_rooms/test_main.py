import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient

from rooms.main import create_app


def test_stranger_cannot_post_and_history_is_ordered():
    client = TestClient(create_app(":memory:"))
    room = client.post("/rooms", json={"title": "склад", "owner": "ada"}).json()
    denied = client.post(f"/rooms/{room['id']}/messages", json={"user_id": "boris", "body": "привет"})
    assert denied.status_code == 403
    client.post(f"/rooms/{room['id']}/join", json={"user_id": "boris"})
    client.post(f"/rooms/{room['id']}/messages", json={"user_id": "ada", "body": "первый"})
    client.post(f"/rooms/{room['id']}/messages", json={"user_id": "boris", "body": "второй"})
    history = client.get(f"/rooms/{room['id']}/messages").json()
    assert [item["body"] for item in history] == ["первый", "второй"]
    client.post(f"/rooms/{room['id']}/presence", json={"user_id": "boris", "online": False})
    assert client.get(f"/rooms/{room['id']}/online").json() == ["ada"]
