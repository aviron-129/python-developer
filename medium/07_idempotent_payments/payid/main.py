import os

from fastapi import FastAPI, Header, HTTPException, Response
from pydantic import BaseModel, Field

from payid.service import AlreadyRefunded, Conflict, Payments, UnknownPayment


class ChargeIn(BaseModel):
    amount: int = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)


def create_app(database: str | None = None) -> FastAPI:
    payments = Payments(database or os.environ.get("DATABASE_PATH", ":memory:"))
    app = FastAPI(title="Idempotent Payments")

    @app.post("/payments", status_code=201)
    def charge(body: ChargeIn, response: Response, idempotency_key: str = Header(alias="Idempotency-Key")):
        try:
            payment, replayed = payments.charge(idempotency_key, body.amount, body.currency.upper())
        except Conflict as exc:
            raise HTTPException(409, {"code": "idempotency_conflict"}) from exc
        if replayed:
            response.status_code = 200
        response.headers["Idempotent-Replayed"] = "true" if replayed else "false"
        return payment

    @app.get("/payments/{payment_id}")
    def read_payment(payment_id: str):
        try:
            return payments.get(payment_id)
        except UnknownPayment as exc:
            raise HTTPException(404, {"code": "unknown_payment"}) from exc

    @app.post("/payments/{payment_id}/refund")
    def refund(payment_id: str):
        try:
            return payments.refund(payment_id)
        except UnknownPayment as exc:
            raise HTTPException(404, {"code": "unknown_payment"}) from exc
        except AlreadyRefunded as exc:
            raise HTTPException(409, {"code": "already_refunded"}) from exc

    return app


app = create_app()
