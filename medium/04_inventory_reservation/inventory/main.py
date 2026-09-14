import os

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from inventory.domain import (
    IllegalTransition,
    InsufficientStock,
    UnknownReservation,
    UnknownSku,
    VersionConflict,
)
from inventory.ledger import Ledger


class ItemIn(BaseModel):
    sku: str = Field(min_length=1)
    name: str = Field(min_length=1)
    on_hand: int = Field(ge=0)


class ReceiveIn(BaseModel):
    qty: int = Field(gt=0)


class ReserveIn(BaseModel):
    sku: str
    qty: int = Field(gt=0)
    order_ref: str = Field(min_length=1)


def create_app(database: str | None = None) -> FastAPI:
    ledger = Ledger(database or os.environ.get("DATABASE_PATH", ":memory:"))
    app = FastAPI(title="Inventory Reservation")
    app.state.ledger = ledger

    @app.post("/items", status_code=201)
    def add_item(body: ItemIn):
        try:
            return ledger.add_item(body.sku, body.name, body.on_hand)
        except Exception as exc:
            if "UNIQUE" in str(exc):
                raise HTTPException(409, {"code": "sku_exists"}) from exc
            raise

    @app.get("/items/{sku}")
    def read_item(sku: str):
        try:
            return ledger.item(sku)
        except UnknownSku as exc:
            raise HTTPException(404, {"code": "unknown_sku"}) from exc

    @app.post("/items/{sku}/receive")
    def receive(sku: str, body: ReceiveIn, if_match: int = Header(alias="If-Match")):
        try:
            return ledger.receive(sku, body.qty, if_match)
        except UnknownSku as exc:
            raise HTTPException(404, {"code": "unknown_sku"}) from exc
        except VersionConflict as exc:
            raise HTTPException(409, {"code": "version_conflict", "sku": exc.sku}) from exc

    @app.post("/reservations", status_code=201)
    def reserve(body: ReserveIn):
        try:
            return ledger.reserve(body.sku, body.qty, body.order_ref)
        except UnknownSku as exc:
            raise HTTPException(404, {"code": "unknown_sku"}) from exc
        except InsufficientStock as exc:
            raise HTTPException(
                409,
                {"code": "insufficient_stock", "available": exc.available, "requested": exc.requested},
            ) from exc
        except VersionConflict as exc:
            raise HTTPException(409, {"code": "version_conflict"}) from exc

    @app.post("/reservations/{reservation_id}/commit")
    def commit(reservation_id: str):
        return _finish(lambda: ledger.commit(reservation_id))

    @app.post("/reservations/{reservation_id}/release")
    def release(reservation_id: str):
        return _finish(lambda: ledger.release(reservation_id))

    return app


def _finish(call):
    try:
        return call()
    except UnknownReservation as exc:
        raise HTTPException(404, {"code": "unknown_reservation"}) from exc
    except IllegalTransition as exc:
        raise HTTPException(409, {"code": "illegal_transition", "status": exc.status}) from exc


app = create_app()
