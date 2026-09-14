import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from apikeys.service import Forbidden, KeyStore, UnknownKey


class IssueIn(BaseModel):
    name: str
    scopes: list[str] = Field(min_length=1)


class AuthIn(BaseModel):
    token: str
    scope: str


def create_app(database: str | None = None) -> FastAPI:
    store = KeyStore(database or os.environ.get("DATABASE_PATH", ":memory:"))
    app = FastAPI(title="API Keys")

    @app.post("/keys", status_code=201)
    def issue(body: IssueIn):
        return store.issue(body.name, body.scopes)

    @app.post("/keys/{key_id}/rotate")
    def rotate(key_id: str):
        try:
            return store.rotate(key_id)
        except UnknownKey as exc:
            raise HTTPException(404, {"code": "unknown_key"}) from exc

    @app.post("/keys/{key_id}/revoke")
    def revoke(key_id: str):
        try:
            return store.revoke(key_id)
        except UnknownKey as exc:
            raise HTTPException(404, {"code": "unknown_key"}) from exc

    @app.post("/authorize")
    def authorize(body: AuthIn):
        try:
            return store.authorize(body.token, body.scope)
        except Forbidden as exc:
            raise HTTPException(403, {"code": "forbidden"}) from exc

    return app


app = create_app()
