import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient

from suggest.main import create_app


def test_prefix_synonym_and_typo():
    client = TestClient(create_app())
    client.post("/items", json={"name": "Кружка", "synonyms": ["mug"]})
    client.post("/items", json={"name": "Чашка", "synonyms": []})
    assert client.get("/suggest", params={"q": "кру"}).json() == ["Кружка"]
    assert client.get("/suggest", params={"q": "mug"}).json() == ["Кружка"]
    assert client.get("/suggest", params={"q": "чашкв"}).json() == ["Чашка"]
