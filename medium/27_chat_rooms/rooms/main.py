import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


class RoomIn(BaseModel):
    title: str
    owner: str


class JoinIn(BaseModel):
    user_id: str


class PresenceIn(BaseModel):
    user_id: str
    online: bool


class MessageIn(BaseModel):
    user_id: str
    body: str


def create_app(database: str | None = None) -> FastAPI:
    from rooms.service import NotMember, Rooms, UnknownRoom

    rooms = Rooms(database or os.environ.get("DATABASE_PATH", ":memory:"))
    app = FastAPI(title="Chat Rooms")

    @app.post("/rooms", status_code=201)
    def create(body: RoomIn):
        return rooms.create(body.title, body.owner)

    @app.post("/rooms/{room_id}/join")
    def join(room_id: str, body: JoinIn):
        try:
            return rooms.join(room_id, body.user_id)
        except UnknownRoom as exc:
            raise HTTPException(404, {"code": "unknown_room"}) from exc

    @app.post("/rooms/{room_id}/presence")
    def presence(room_id: str, body: PresenceIn):
        try:
            return rooms.presence(room_id, body.user_id, body.online)
        except NotMember as exc:
            raise HTTPException(403, {"code": "not_member"}) from exc

    @app.post("/rooms/{room_id}/messages", status_code=201)
    def post(room_id: str, body: MessageIn):
        try:
            return rooms.post(room_id, body.user_id, body.body)
        except NotMember as exc:
            raise HTTPException(403, {"code": "not_member"}) from exc

    @app.get("/rooms/{room_id}/messages")
    def history(room_id: str):
        return rooms.history(room_id)

    @app.get("/rooms/{room_id}/online")
    def online(room_id: str):
        return rooms.online(room_id)

    return app


app = create_app()
