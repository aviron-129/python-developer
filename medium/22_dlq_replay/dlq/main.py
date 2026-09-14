import os

from fastapi import FastAPI
from pydantic import BaseModel


class JobIn(BaseModel):
    payload: dict


def create_app(database: str | None = None) -> FastAPI:
    from dlq.service import Queue

    queue = Queue(database or os.environ.get("DATABASE_PATH", ":memory:"))
    app = FastAPI(title="DLQ Replay")

    @app.post("/jobs", status_code=201)
    def enqueue(body: JobIn):
        return queue.enqueue(body.payload)

    @app.post("/workers/tick")
    def tick():
        return queue.work()

    @app.get("/dead")
    def dead():
        return queue.dead()

    @app.post("/dead/{job_id}/replay")
    def replay(job_id: str):
        return queue.replay(job_id)

    return app


app = create_app()
