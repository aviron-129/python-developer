import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient

from breaker.main import create_app


def client():
    return TestClient(create_app())


def test_opens_after_threshold_and_serves_cache():
    api = client()
    api.put("/upstreams/billing", json={"fail": False, "body": {"invoice": "A-1"}})
    ok = api.post("/calls", json={"service": "billing"})
    assert ok.json()["source"] == "upstream"
    api.put("/upstreams/billing", json={"fail": True, "body": {}})
    for _ in range(3):
        assert api.post("/calls", json={"service": "billing"}).status_code == 502
    assert api.get("/circuits/billing").json()["state"] == "open"
    cached = api.post("/calls", json={"service": "billing"})
    assert cached.status_code == 200
    assert cached.json()["source"] == "cache"
    assert cached.json()["body"] == {"invoice": "A-1"}
    assert cached.json()["calls"] == 4
    assert api.post("/calls", json={"service": "billing"}).json()["calls"] == 4


def test_open_without_cache_is_503():
    api = client()
    api.put("/upstreams/mail", json={"fail": True, "body": {}})
    for _ in range(3):
        assert api.post("/calls", json={"service": "mail"}).status_code == 502
    blocked = api.post("/calls", json={"service": "mail"})
    assert blocked.status_code == 503
    assert blocked.json()["detail"]["code"] == "circuit_open"


def test_half_open_success_closes_and_failure_reopens():
    api = client()
    api.put("/upstreams/pay", json={"fail": True, "body": {}})
    for _ in range(3):
        api.post("/calls", json={"service": "pay"})
    api.post("/clock", json={"seconds": 30})
    api.put("/upstreams/pay", json={"fail": False, "body": {"ok": True}})
    probed = api.post("/calls", json={"service": "pay"})
    assert probed.json()["source"] == "upstream"
    assert api.get("/circuits/pay").json()["state"] == "closed"

    api.put("/upstreams/pay", json={"fail": True, "body": {}})
    for _ in range(3):
        api.post("/calls", json={"service": "pay"})
    assert api.get("/circuits/pay").json()["state"] == "open"
    api.post("/clock", json={"seconds": 30})
    failed_probe = api.post("/calls", json={"service": "pay"})
    assert failed_probe.status_code == 502
    assert api.get("/circuits/pay").json()["state"] == "open"
