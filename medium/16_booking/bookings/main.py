import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


class ResourceIn(BaseModel):
    code: str
    name: str


class BookIn(BaseModel):
    resource: str
    start_at: str
    end_at: str
    guest: str


def create_app(database: str | None = None) -> FastAPI:
    from bookings.service import Calendar, Overlap, UnknownBooking

    calendar = Calendar(database or os.environ.get("DATABASE_PATH", ":memory:"))
    app = FastAPI(title="Booking")

    @app.post("/resources", status_code=201)
    def resources(body: ResourceIn):
        return calendar.add_resource(body.code, body.name)

    @app.post("/bookings", status_code=201)
    def book(body: BookIn):
        try:
            return calendar.book(body.resource, body.start_at, body.end_at, body.guest)
        except Overlap as exc:
            raise HTTPException(409, {"code": "overlap"}) from exc

    @app.post("/bookings/{booking_id}/cancel")
    def cancel(booking_id: str):
        try:
            return calendar.cancel(booking_id)
        except UnknownBooking as exc:
            raise HTTPException(404, {"code": "unknown_booking"}) from exc

    return app


app = create_app()
