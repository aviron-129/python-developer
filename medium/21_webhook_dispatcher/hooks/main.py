import os

from fastapi import FastAPI
from pydantic import BaseModel, Field


class SubIn(BaseModel):
    event_type: str
    target: str
    secret: str
    fail_times: int = Field(ge=0, default=0)


class EmitIn(BaseModel):
    event_type: str
    payload: dict


def create_app(database: str | None = None) -> FastAPI:
    from hooks.service import Dispatcher

    dispatcher = Dispatcher(database or os.environ.get("DATABASE_PATH", ":memory:"))
    app = FastAPI(title="Webhook Dispatcher")
    app.state.dispatcher = dispatcher

    @app.post("/subscriptions", status_code=201)
    def subscribe(body: SubIn):
        return dispatcher.subscribe(body.event_type, body.target, body.secret, body.fail_times)

    @app.post("/events")
    def emit(body: EmitIn):
        return dispatcher.emit(body.event_type, body.payload)

    return app


app = create_app()
