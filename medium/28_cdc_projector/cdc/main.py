import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


class CreateIn(BaseModel):
    sku: str
    total: int = Field(gt=0)


class UpdateIn(BaseModel):
    total: int = Field(gt=0)


def create_app(database: str | None = None) -> FastAPI:
    from cdc.service import Source, UnknownOrder

    source = Source(database or os.environ.get("DATABASE_PATH", ":memory:"))
    app = FastAPI(title="CDC Projector")

    @app.post("/orders", status_code=201)
    def create(body: CreateIn):
        return source.create(body.sku, body.total)

    @app.patch("/orders/{order_id}")
    def update(order_id: str, body: UpdateIn):
        try:
            return source.update(order_id, body.total)
        except UnknownOrder as exc:
            raise HTTPException(404, {"code": "unknown_order"}) from exc

    @app.delete("/orders/{order_id}")
    def delete(order_id: str):
        try:
            return source.delete(order_id)
        except UnknownOrder as exc:
            raise HTTPException(404, {"code": "unknown_order"}) from exc

    @app.post("/project")
    def project():
        return source.project()

    @app.get("/views/orders")
    def view():
        return source.view()

    return app


app = create_app()
