import base64
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient

from uploads.main import create_app


def test_png_becomes_ready_and_other_bytes_are_rejected():
    client = TestClient(create_app(":memory:"))
    good = client.post("/uploads", json={"filename": "a.png"}).json()
    png = b"\x89PNG" + b"tiny"
    client.put(f"/uploads/{good['id']}/content", json={"content_base64": base64.b64encode(png).decode()})
    ready = client.post(f"/uploads/{good['id']}/process")
    assert ready.json()["status"] == "ready"
    assert ready.json()["detail"] == "preview:8"

    bad = client.post("/uploads", json={"filename": "b.txt"}).json()
    client.put(
        f"/uploads/{bad['id']}/content",
        json={"content_base64": base64.b64encode(b"hello").decode()},
    )
    rejected = client.post(f"/uploads/{bad['id']}/process")
    assert rejected.json()["status"] == "rejected"
