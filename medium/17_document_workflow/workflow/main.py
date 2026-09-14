import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


class DocIn(BaseModel):
    title: str
    author: str


class ActIn(BaseModel):
    actor: str


def create_app(database: str | None = None) -> FastAPI:
    from workflow.service import Documents, WorkflowError

    docs = Documents(database or os.environ.get("DATABASE_PATH", ":memory:"))
    app = FastAPI(title="Document Workflow")

    def run(call):
        try:
            return call()
        except WorkflowError as exc:
            status = 404 if exc.code == "unknown_document" else 409
            raise HTTPException(status, {"code": exc.code}) from exc

    @app.post("/documents", status_code=201)
    def create(body: DocIn):
        return docs.create(body.title, body.author)

    @app.post("/documents/{doc_id}/submit")
    def submit(doc_id: str, body: ActIn):
        return run(lambda: docs.act(doc_id, "submit", body.actor))

    @app.post("/documents/{doc_id}/approve")
    def approve(doc_id: str, body: ActIn):
        return run(lambda: docs.act(doc_id, "approve", body.actor))

    @app.post("/documents/{doc_id}/reject")
    def reject(doc_id: str, body: ActIn):
        return run(lambda: docs.act(doc_id, "reject", body.actor))

    @app.post("/documents/{doc_id}/publish")
    def publish(doc_id: str, body: ActIn):
        return run(lambda: docs.act(doc_id, "publish", body.actor))

    return app


app = create_app()
