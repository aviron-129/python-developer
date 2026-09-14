import os

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel


class NoteIn(BaseModel):
    body: str


def create_app(database: str | None = None) -> FastAPI:
    from tenants.service import MissingTenant, Notes, UnknownNote

    notes = Notes(database or os.environ.get("DATABASE_PATH", ":memory:"))
    app = FastAPI(title="Multi-tenant Notes")

    def tenant_of(header: str | None) -> str:
        if not header:
            raise HTTPException(400, {"code": "missing_tenant"})
        return header

    @app.post("/notes", status_code=201)
    def add(body: NoteIn, x_tenant: str | None = Header(default=None)):
        try:
            return notes.add(tenant_of(x_tenant), body.body)
        except MissingTenant as exc:
            raise HTTPException(400, {"code": "missing_tenant"}) from exc

    @app.get("/notes")
    def listing(x_tenant: str | None = Header(default=None)):
        return notes.list_for(tenant_of(x_tenant))

    @app.get("/notes/{note_id}")
    def read(note_id: str, x_tenant: str | None = Header(default=None)):
        try:
            return notes.read(tenant_of(x_tenant), note_id)
        except UnknownNote as exc:
            raise HTTPException(404, {"code": "unknown_note"}) from exc

    return app


app = create_app()
