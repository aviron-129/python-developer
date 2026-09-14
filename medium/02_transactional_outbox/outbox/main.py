import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from outbox.ledger import Ledger


class OrderIn(BaseModel):
    customer: str = Field(min_length=1)
    sku: str = Field(min_length=1)
    total: int = Field(gt=0)


class Envelope(BaseModel):
    message_id: str
    event_type: str
    payload: dict


def create_app(database: str | None = None) -> FastAPI:
    ledger = Ledger(database or os.environ.get("DATABASE_PATH", ":memory:"))
    app = FastAPI(title="Transactional Outbox")
    app.state.ledger = ledger

    @app.post("/orders", status_code=201)
    def place(body: OrderIn):
        placed = ledger.place(body.customer, body.sku, body.total)
        order = ledger.order(placed["order_id"])
        return {**dict(order), "message_id": placed["message_id"]}

    @app.get("/orders/{order_id}")
    def read_order(order_id: str):
        row = ledger.order(order_id)
        if row is None:
            raise HTTPException(404, {"code": "unknown_order"})
        return dict(row)

    @app.get("/outbox")
    def outbox():
        return ledger.pending()

    @app.post("/relay/tick")
    def tick():
        delivered = ledger.relay()
        return {"delivered": delivered, "invoices": ledger.invoices()}

    @app.post("/billing/consume")
    def consume(body: Envelope):
        status = ledger.accept(body.message_id, body.event_type, body.payload)
        return {"status": status, "invoices": ledger.invoices()}

    @app.get("/billing/invoices")
    def invoices():
        return ledger.invoices()

    return app


app = create_app()
