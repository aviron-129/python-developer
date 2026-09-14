import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient

from oauth.main import create_app


def ready():
    api = TestClient(create_app(":memory:"))
    api.post("/users", json={"email": "ada@example.com", "password": "correct-horse"})
    client = api.post(
        "/clients",
        json={"name": "shop", "redirect_uri": "https://shop.example/callback"},
    ).json()
    return api, client


def login(api, client, scope="profile"):
    code = api.post(
        "/oauth/authorize",
        json={
            "email": "ada@example.com",
            "password": "correct-horse",
            "client_id": client["client_id"],
            "redirect_uri": client["redirect_uri"],
            "scope": scope,
        },
    )
    assert code.status_code == 200
    tokens = api.post(
        "/oauth/token",
        json={
            "grant_type": "authorization_code",
            "code": code.json()["code"],
            "client_id": client["client_id"],
            "client_secret": client["client_secret"],
            "redirect_uri": client["redirect_uri"],
        },
    )
    assert tokens.status_code == 200
    return tokens.json()


def test_authorization_code_then_userinfo():
    api, client = ready()
    tokens = login(api, client)
    me = api.get("/userinfo", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert me.status_code == 200
    assert me.json()["email"] == "ada@example.com"


def test_code_is_single_use_and_redirect_is_bound():
    api, client = ready()
    issued = api.post(
        "/oauth/authorize",
        json={
            "email": "ada@example.com",
            "password": "correct-horse",
            "client_id": client["client_id"],
            "redirect_uri": client["redirect_uri"],
            "scope": "profile",
        },
    ).json()
    wrong = api.post(
        "/oauth/token",
        json={
            "grant_type": "authorization_code",
            "code": issued["code"],
            "client_id": client["client_id"],
            "client_secret": client["client_secret"],
            "redirect_uri": "https://evil.example/callback",
        },
    )
    assert wrong.status_code == 400
    assert wrong.json()["detail"]["code"] == "invalid_code"
    ok = api.post(
        "/oauth/token",
        json={
            "grant_type": "authorization_code",
            "code": issued["code"],
            "client_id": client["client_id"],
            "client_secret": client["client_secret"],
            "redirect_uri": client["redirect_uri"],
        },
    )
    assert ok.status_code == 200
    again = api.post(
        "/oauth/token",
        json={
            "grant_type": "authorization_code",
            "code": issued["code"],
            "client_id": client["client_id"],
            "client_secret": client["client_secret"],
            "redirect_uri": client["redirect_uri"],
        },
    )
    assert again.json()["detail"]["code"] == "invalid_code"


def test_refresh_rotates_and_reuse_revokes_family():
    api, client = ready()
    tokens = login(api, client)
    rotated = api.post(
        "/oauth/token",
        json={
            "grant_type": "refresh_token",
            "refresh_token": tokens["refresh_token"],
            "client_id": client["client_id"],
            "client_secret": client["client_secret"],
        },
    )
    assert rotated.status_code == 200
    reused = api.post(
        "/oauth/token",
        json={
            "grant_type": "refresh_token",
            "refresh_token": tokens["refresh_token"],
            "client_id": client["client_id"],
            "client_secret": client["client_secret"],
        },
    )
    assert reused.json()["detail"]["code"] == "refresh_reused"
    blocked = api.get(
        "/userinfo",
        headers={"Authorization": f"Bearer {rotated.json()['access_token']}"},
    )
    assert blocked.status_code == 401


def test_missing_profile_scope_cannot_read_email():
    api, client = ready()
    tokens = login(api, client, scope="orders")
    me = api.get("/userinfo", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert me.status_code == 403
    assert me.json()["detail"]["code"] == "insufficient_scope"
