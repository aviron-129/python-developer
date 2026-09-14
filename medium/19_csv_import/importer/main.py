import os

from fastapi import FastAPI
from pydantic import BaseModel


class ImportIn(BaseModel):
    csv: str


def create_app(database: str | None = None) -> FastAPI:
    from importer.service import Importer

    tool = Importer(database or os.environ.get("DATABASE_PATH", ":memory:"))
    app = FastAPI(title="CSV Import")

    @app.post("/imports")
    def load(body: ImportIn):
        return tool.load(body.csv)

    @app.get("/products")
    def products():
        return tool.products()

    return app


app = create_app()
