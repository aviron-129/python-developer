import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient

from hooks.main import create_app
from hooks.service import sign


def test_retries_then_signs_payload():
    app = create_app(":memory:")
    client = TestClient(app)
    client.post(
        "/subscriptions",
        json={"event_type": "order.placed", "target": "shop", "secret": "topsecret", "fail_times": 2},
    )
    result = client.post("/events", json={"event_type": "order.placed", "payload": {"id": "o-1"}})
    assert result.json()[0]["status"] == "delivered"
    assert result.json()[0]["attempts"] == 3
    seen = app.state.dispatcher.sinks["shop"]["seen"]
    assert len(seen) == 1
    body = json.dumps({"id": "o-1"}, sort_keys=True)
    assert seen[0]["signature"] == sign("topsecret", body)
