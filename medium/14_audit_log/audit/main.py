import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from audit.service import AuditLog, BrokenChain


class EventIn(BaseModel):
    actor: str
    action: str
    subject: str
    at: str


def create_app(database: str | None = None) -> FastAPI:
    log = AuditLog(database or os.environ.get("DATABASE_PATH", ":memory:"))
    app = FastAPI(title="Audit Log")

    @app.post("/events", status_code=201)
    def append(body: EventIn):
        return log.append(body.actor, body.action, body.subject, body.at)

    @app.get("/events")
    def events(actor: str | None = None, action: str | None = None):
        return log.query(actor, action)

    @app.get("/events/verify")
    def verify():
        try:
            return log.verify()
        except BrokenChain as exc:
            raise HTTPException(409, {"code": "broken_chain"}) from exc

    @app.put("/events/{event_id}")
    def reject_update(event_id: str):
        raise HTTPException(405, {"code": "append_only", "id": event_id})

    return app


app = create_app()
