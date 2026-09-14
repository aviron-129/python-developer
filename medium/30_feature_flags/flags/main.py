import os

from fastapi import FastAPI
from pydantic import BaseModel, Field


class FlagIn(BaseModel):
    name: str
    percent: int = Field(ge=0, le=100)
    allow_tenants: list[str] = []


class EvalIn(BaseModel):
    user_id: str
    tenant: str = ""


def create_app(database: str | None = None) -> FastAPI:
    from flags.service import Flags

    flags = Flags(database or os.environ.get("DATABASE_PATH", ":memory:"))
    app = FastAPI(title="Feature Flags")

    @app.put("/flags/{name}")
    def put(name: str, body: FlagIn):
        return flags.put(name, body.percent, body.allow_tenants)

    @app.post("/flags/{name}/evaluate")
    def evaluate(name: str, body: EvalIn):
        return flags.evaluate(name, body.user_id, body.tenant)

    return app


app = create_app()
