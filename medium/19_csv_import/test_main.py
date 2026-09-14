import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient

from importer.main import create_app


def test_partial_import_keeps_valid_rows():
    client = TestClient(create_app(":memory:"))
    text = "mug,Кружка,4\nbad,Без числа,x\nmug,Дубль,1\ncup,Чашка,2\n"
    result = client.post("/imports", json={"csv": text})
    assert result.status_code == 200
    assert [item["sku"] for item in result.json()["accepted"]] == ["mug", "cup"]
    assert [item["reason"] for item in result.json()["errors"]] == ["invalid_row", "duplicate"]
    assert len(client.get("/products").json()) == 2
