import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from quotas.service import QuotaExceeded, Quotas, UnknownAccount


class AccountIn(BaseModel):
    name: str
    monthly_limit: int = Field(gt=0)


class UsageIn(BaseModel):
    units: int = Field(gt=0)


def create_app(database: str | None = None) -> FastAPI:
    quotas = Quotas(database or os.environ.get("DATABASE_PATH", ":memory:"))
    app = FastAPI(title="Usage Quotas")

    @app.post("/accounts", status_code=201)
    def accounts(body: AccountIn):
        return quotas.open_account(body.name, body.monthly_limit)

    @app.post("/accounts/{account_id}/usage")
    def usage(account_id: str, body: UsageIn):
        try:
            return quotas.consume(account_id, body.units)
        except UnknownAccount as exc:
            raise HTTPException(404, {"code": "unknown_account"}) from exc
        except QuotaExceeded as exc:
            raise HTTPException(
                429,
                {"code": "quota_exceeded", "used": exc.used, "limit": exc.limit, "requested": exc.requested},
            ) from exc

    @app.post("/accounts/{account_id}/close-period")
    def close_period(account_id: str):
        try:
            return quotas.close_period(account_id)
        except UnknownAccount as exc:
            raise HTTPException(404, {"code": "unknown_account"}) from exc

    @app.get("/accounts/{account_id}")
    def read_account(account_id: str):
        try:
            return quotas.get(account_id)
        except UnknownAccount as exc:
            raise HTTPException(404, {"code": "unknown_account"}) from exc

    return app


app = create_app()
