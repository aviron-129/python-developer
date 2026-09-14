import os

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel


class LoginIn(BaseModel):
    user_id: str
    device: str


def create_app(database: str | None = None) -> FastAPI:
    from sessions.service import Sessions, UnknownSession

    store = Sessions(database or os.environ.get("DATABASE_PATH", ":memory:"))
    app = FastAPI(title="Sessions")

    @app.post("/login", status_code=201)
    def login(body: LoginIn):
        return store.login(body.user_id, body.device)

    @app.get("/users/{user_id}/sessions")
    def listing(user_id: str):
        return store.list_for(user_id)

    @app.post("/sessions/{session_id}/revoke")
    def revoke(session_id: str):
        try:
            return store.revoke(session_id)
        except UnknownSession as exc:
            raise HTTPException(404, {"code": "unknown_session"}) from exc

    @app.post("/users/{user_id}/revoke-all")
    def revoke_all(user_id: str):
        return store.revoke_all(user_id)

    @app.get("/me")
    def me(authorization: str = Header(default="")):
        _scheme, _, token = authorization.partition(" ")
        try:
            return store.me(token)
        except UnknownSession as exc:
            raise HTTPException(401, {"code": "invalid_session"}) from exc

    return app


app = create_app()
