import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient

from otp.main import create_app


def enrolled():
    client = TestClient(create_app(":memory:"))
    user = client.post("/users", json={"email": "ada@example.com", "password": "correct-horse"}).json()
    started = client.post(f"/users/{user['id']}/enroll").json()
    code = client.get(f"/users/{user['id']}/current-code").json()["code"]
    assert client.post(f"/users/{user['id']}/confirm", json={"code": code}).status_code == 200
    return client, user, started


def test_login_accepts_current_totp():
    client, _user, _started = enrolled()
    code = client.get(f"/users/{_user['id']}/current-code").json()["code"]
    logged = client.post("/login", json={"email": "ada@example.com", "password": "correct-horse", "code": code})
    assert logged.status_code == 200
    assert logged.json()["email"] == "ada@example.com"


def test_backup_code_works_once():
    client, user, started = enrolled()
    backup = started["backup_codes"][0]
    first = client.post("/login", json={"email": "ada@example.com", "password": "correct-horse", "code": backup})
    second = client.post("/login", json={"email": "ada@example.com", "password": "correct-horse", "code": backup})
    assert first.status_code == 200
    assert second.status_code == 401
    assert second.json()["detail"]["code"] == "invalid_code"
    assert user["id"]
