import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from promos.service import PromoError, Promos


class CodeIn(BaseModel):
    code: str
    kind: str
    value: int = Field(gt=0)
    max_uses: int = Field(gt=0)
    expires_on: str
    referrer: str | None = None


class RedeemIn(BaseModel):
    user_id: str
    amount: int = Field(gt=0)
    today: str


def create_app(database: str | None = None) -> FastAPI:
    promos = Promos(database or os.environ.get("DATABASE_PATH", ":memory:"))
    app = FastAPI(title="Promo Codes")

    @app.post("/codes", status_code=201)
    def codes(body: CodeIn):
        if body.kind not in {"fixed", "percent"}:
            raise HTTPException(422, {"code": "bad_kind"})
        return promos.create(body.code, body.kind, body.value, body.max_uses, body.expires_on, body.referrer)

    @app.post("/codes/{code}/redeem")
    def redeem(code: str, body: RedeemIn):
        try:
            return promos.redeem(code, body.user_id, body.amount, body.today)
        except PromoError as exc:
            status = 404 if exc.code == "unknown_code" else 409
            raise HTTPException(status, {"code": exc.code}) from exc

    return app


app = create_app()
