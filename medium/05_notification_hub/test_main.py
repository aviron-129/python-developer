import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient

from notify.main import create_app


def client():
    app = create_app(":memory:")
    return TestClient(app), app


def test_muted_telegram_is_not_sent():
    api, app = client()
    person = api.post(
        "/recipients",
        json={
            "name": "Нина",
            "email": "nina@example.com",
            "push_token": "push-1",
            "telegram_chat": "chat-9",
        },
    ).json()
    api.put(f"/recipients/{person['id']}/preferences", json={"telegram": False})
    api.post("/templates", json={"code": "order_ready", "body": "Заказ {order_id} собран"})
    sent = api.post(
        "/notifications",
        json={"recipient_id": person["id"], "template": "order_ready", "payload": {"order_id": "A-14"}},
    )
    assert sent.status_code == 201
    body = sent.json()
    assert body["status"] == "dispatched"
    by_channel = {item["channel"]: item for item in body["deliveries"]}
    assert by_channel["telegram"]["status"] == "skipped"
    assert by_channel["email"]["status"] == "sent"
    assert by_channel["email"]["detail"]
    channels = [item["channel"] for item in app.state.bus.sent]
    assert channels == ["email", "push"]
    assert app.state.bus.sent[0]["body"] == "Заказ A-14 собран"
    assert app.state.bus.sent[0]["address"] == "nina@example.com"


def test_all_muted_is_suppressed_without_calls():
    api, app = client()
    person = api.post(
        "/recipients",
        json={
            "name": "Илья",
            "email": "ilya@example.com",
            "push_token": "push-2",
            "telegram_chat": "chat-2",
        },
    ).json()
    api.put(
        f"/recipients/{person['id']}/preferences",
        json={"email": False, "push": False, "telegram": False},
    )
    api.post("/templates", json={"code": "ping", "body": "Привет, {name}"})
    sent = api.post(
        "/notifications",
        json={"recipient_id": person["id"], "template": "ping", "payload": {"name": "Илья"}},
    )
    assert sent.json()["status"] == "suppressed"
    assert app.state.bus.sent == []


def test_missing_placeholder_does_not_create_notification():
    api, _app = client()
    person = api.post(
        "/recipients",
        json={
            "name": "Оля",
            "email": "olya@example.com",
            "push_token": "push-3",
            "telegram_chat": "chat-3",
        },
    ).json()
    api.post("/templates", json={"code": "ping", "body": "Заказ {order_id}"})
    failed = api.post(
        "/notifications",
        json={"recipient_id": person["id"], "template": "ping", "payload": {}},
    )
    assert failed.status_code == 422
    assert failed.json()["detail"]["code"] == "missing_placeholder"
