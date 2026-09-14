from fastapi import FastAPI
from pydantic import BaseModel


class ItemIn(BaseModel):
    name: str
    synonyms: list[str] = []


class QueryIn(BaseModel):
    q: str


def create_app() -> FastAPI:
    from suggest.service import Catalog

    catalog = Catalog()
    app = FastAPI(title="Autocomplete")

    @app.post("/items", status_code=201)
    def add(body: ItemIn):
        return catalog.add(body.name, body.synonyms)

    @app.get("/suggest")
    def suggest(q: str = ""):
        return catalog.search(q)

    return app


app = create_app()
