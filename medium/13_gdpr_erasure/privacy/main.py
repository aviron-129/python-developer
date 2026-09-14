import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from privacy.service import Privacy, UnknownUser


class UserIn(BaseModel):
    name: str
    email: str


class OrderIn(BaseModel):
    title: str
    total: int = Field(gt=0)


def create_app(database: str | None = None) -> FastAPI:
    privacy = Privacy(database or os.environ.get("DATABASE_PATH", ":memory:"))
    app = FastAPI(title="GDPR Export and Erasure")

    @app.post("/users", status_code=201)
    def users(body: UserIn):
        return privacy.add_user(body.name, body.email)

    @app.post("/users/{user_id}/orders", status_code=201)
    def orders(user_id: str, body: OrderIn):
        try:
            return privacy.add_order(user_id, body.title, body.total)
        except UnknownUser as exc:
            raise HTTPException(404, {"code": "unknown_user"}) from exc

    @app.post("/users/{user_id}/export", status_code=201)
    def export(user_id: str):
        try:
            return privacy.export(user_id)
        except UnknownUser as exc:
            raise HTTPException(404, {"code": "unknown_user"}) from exc

    @app.post("/users/{user_id}/erase")
    def erase(user_id: str):
        try:
            return privacy.erase(user_id)
        except UnknownUser as exc:
            raise HTTPException(404, {"code": "unknown_user"}) from exc

    return app


app = create_app()
