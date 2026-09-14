import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from notify.domain import MissingPlaceholder, UnknownRecipient, UnknownTemplate
from notify.hub import Hub, RecordingBus


class RecipientIn(BaseModel):
    name: str
    email: str
    push_token: str
    telegram_chat: str


class PreferencesIn(BaseModel):
    email: bool | None = None
    push: bool | None = None
    telegram: bool | None = None


class TemplateIn(BaseModel):
    code: str = Field(min_length=1)
    body: str = Field(min_length=1)


class NotifyIn(BaseModel):
    recipient_id: str
    template: str
    payload: dict


def create_app(database: str | None = None) -> FastAPI:
    bus = RecordingBus()
    hub = Hub(database or os.environ.get("DATABASE_PATH", ":memory:"), bus)
    app = FastAPI(title="Notification Hub")
    app.state.hub = hub
    app.state.bus = bus

    @app.post("/recipients", status_code=201)
    def recipients(body: RecipientIn):
        return hub.add_recipient(body.name, body.email, body.push_token, body.telegram_chat)

    @app.put("/recipients/{recipient_id}/preferences")
    def preferences(recipient_id: str, body: PreferencesIn):
        enabled = {key: value for key, value in body.model_dump().items() if value is not None}
        try:
            return hub.set_preferences(recipient_id, enabled)
        except UnknownRecipient as exc:
            raise HTTPException(404, {"code": "unknown_recipient"}) from exc

    @app.post("/templates", status_code=201)
    def templates(body: TemplateIn):
        return hub.put_template(body.code, body.body)

    @app.post("/notifications", status_code=201)
    def notifications(body: NotifyIn):
        try:
            return hub.dispatch(body.recipient_id, body.template, body.payload)
        except UnknownRecipient as exc:
            raise HTTPException(404, {"code": "unknown_recipient"}) from exc
        except UnknownTemplate as exc:
            raise HTTPException(404, {"code": "unknown_template"}) from exc
        except MissingPlaceholder as exc:
            raise HTTPException(422, {"code": "missing_placeholder", "name": exc.name}) from exc

    @app.get("/notifications/{notification_id}")
    def read_notification(notification_id: str):
        return hub.notification(notification_id)

    return app


app = create_app()
