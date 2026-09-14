import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


class SchemaIn(BaseModel):
    name: str
    required: list[str]
    optional: list[str] = []


class CheckIn(BaseModel):
    payload: dict


def create_app(database: str | None = None) -> FastAPI:
    from registry.service import Incompatible, InvalidPayload, Registry

    registry = Registry(database or os.environ.get("DATABASE_PATH", ":memory:"))
    app = FastAPI(title="Schema Registry")

    @app.post("/schemas", status_code=201)
    def register(body: SchemaIn):
        try:
            return registry.register(body.name, body.required, body.optional)
        except Incompatible as exc:
            raise HTTPException(409, {"code": exc.reason}) from exc

    @app.post("/schemas/{name}/versions/{version}/validate")
    def validate(name: str, version: int, body: CheckIn):
        try:
            return registry.validate(name, version, body.payload)
        except InvalidPayload as exc:
            raise HTTPException(422, {"code": "invalid_payload", "missing": exc.missing}) from exc
        except Incompatible as exc:
            raise HTTPException(404, {"code": exc.reason}) from exc

    return app


app = create_app()
