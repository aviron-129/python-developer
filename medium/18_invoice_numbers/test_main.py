import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient

from invoices.main import create_app


def test_numbers_do_not_reuse_voided():
    client = TestClient(create_app(":memory:"))
    first = client.post("/invoices", json={"customer": "Ада", "total": 100}).json()
    second = client.post("/invoices", json={"customer": "Берт", "total": 200}).json()
    assert first["number"] == "INV-0001"
    assert second["number"] == "INV-0002"
    voided = client.post("/invoices/INV-0001/void").json()
    third = client.post("/invoices", json={"customer": "Кира", "total": 50}).json()
    assert voided["status"] == "void"
    assert third["number"] == "INV-0003"
