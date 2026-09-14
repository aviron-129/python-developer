import base64
import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


class IntentIn(BaseModel):
    filename: str


class ContentIn(BaseModel):
    content_base64: str


def create_app(database: str | None = None) -> FastAPI:
    from uploads.service import UnknownUpload, Uploads

    uploads = Uploads(database or os.environ.get("DATABASE_PATH", ":memory:"))
    app = FastAPI(title="Upload Pipeline")

    @app.post("/uploads", status_code=201)
    def intent(body: IntentIn):
        return uploads.intent(body.filename)

    @app.put("/uploads/{upload_id}/content")
    def store(upload_id: str, body: ContentIn):
        try:
            return uploads.store(upload_id, base64.b64decode(body.content_base64))
        except UnknownUpload as exc:
            raise HTTPException(404, {"code": "unknown_upload"}) from exc

    @app.post("/uploads/{upload_id}/process")
    def process(upload_id: str):
        try:
            return uploads.process(upload_id)
        except UnknownUpload as exc:
            raise HTTPException(404, {"code": "unknown_upload"}) from exc

    return app


app = create_app()
