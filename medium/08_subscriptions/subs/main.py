import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from subs.service import Clock, Subscriptions, UnknownPlan, UnknownSubscription


class PlanIn(BaseModel):
    code: str
    price: int = Field(gt=0)
    trial_days: int = Field(ge=0)


class SubIn(BaseModel):
    plan_code: str
    card_token: str


class AdvanceIn(BaseModel):
    days: int = Field(gt=0)


def create_app(database: str | None = None) -> FastAPI:
    billing = Subscriptions(database or os.environ.get("DATABASE_PATH", ":memory:"), Clock())
    app = FastAPI(title="Subscriptions")

    @app.post("/plans", status_code=201)
    def plans(body: PlanIn):
        return billing.add_plan(body.code, body.price, body.trial_days)

    @app.post("/subscriptions", status_code=201)
    def subscribe(body: SubIn):
        try:
            return billing.subscribe(body.plan_code, body.card_token)
        except UnknownPlan as exc:
            raise HTTPException(404, {"code": "unknown_plan"}) from exc

    @app.post("/clock")
    def clock(body: AdvanceIn):
        billing.clock.advance(body.days)
        return {"now": billing.clock.now.isoformat()}

    @app.post("/billing/run")
    def run():
        return billing.run_billing()

    @app.post("/subscriptions/{sub_id}/cancel")
    def cancel(sub_id: str):
        try:
            return billing.cancel(sub_id)
        except UnknownSubscription as exc:
            raise HTTPException(404, {"code": "unknown_subscription"}) from exc

    @app.get("/subscriptions/{sub_id}")
    def read_sub(sub_id: str):
        try:
            return billing.get(sub_id)
        except UnknownSubscription as exc:
            raise HTTPException(404, {"code": "unknown_subscription"}) from exc

    return app


app = create_app()
