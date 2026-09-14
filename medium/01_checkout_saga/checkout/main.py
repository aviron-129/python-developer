import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from checkout.domain import OutOfStock, UnknownCheckout, UnknownSku
from checkout.services import CheckoutSaga, SandboxPayments
from checkout.store import Store


class SkuIn(BaseModel):
    sku: str = Field(min_length=1)
    name: str = Field(min_length=1)
    on_hand: int = Field(ge=0)


class CheckoutIn(BaseModel):
    sku: str
    qty: int = Field(gt=0)
    amount: int = Field(description="Сумма в копейках")
    card_token: str


def create_app(database: str | None = None) -> FastAPI:
    path = database or os.environ.get("DATABASE_PATH", ":memory:")
    saga = CheckoutSaga(Store(path), SandboxPayments())
    app = FastAPI(title="Checkout Saga")
    app.state.saga = saga

    @app.post("/skus", status_code=201)
    def open_sku(body: SkuIn):
        return saga.open_sku(body.sku, body.name, body.on_hand)

    @app.get("/skus/{sku}")
    def read_sku(sku: str):
        row = saga.store.get_sku(sku)
        if row is None:
            raise HTTPException(404, {"code": "unknown_sku", "sku": sku})
        return dict(row)

    @app.post("/checkouts", status_code=201)
    def start(body: CheckoutIn):
        try:
            return saga.start(body.sku, body.qty, body.amount, body.card_token)
        except UnknownSku as exc:
            raise HTTPException(404, {"code": "unknown_sku", "sku": exc.sku}) from exc
        except OutOfStock as exc:
            raise HTTPException(
                409,
                {
                    "code": "out_of_stock",
                    "sku": exc.sku,
                    "available": exc.available,
                    "requested": exc.requested,
                },
            ) from exc

    @app.get("/checkouts/{checkout_id}")
    def read_checkout(checkout_id: str):
        try:
            return saga.get(checkout_id)
        except UnknownCheckout as exc:
            raise HTTPException(404, {"code": "unknown_checkout"}) from exc

    return app


app = create_app()
