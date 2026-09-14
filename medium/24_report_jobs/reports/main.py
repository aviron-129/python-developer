import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


class ReportIn(BaseModel):
    start_on: str
    end_on: str


def create_app(database: str | None = None) -> FastAPI:
    from reports.service import NotReady, Reports, UnknownReport

    reports = Reports(database or os.environ.get("DATABASE_PATH", ":memory:"))
    app = FastAPI(title="Report Jobs")

    @app.post("/reports", status_code=201)
    def start(body: ReportIn):
        return reports.start(body.start_on, body.end_on)

    @app.post("/reports/{report_id}/tick")
    def tick(report_id: str):
        try:
            return reports.tick(report_id)
        except UnknownReport as exc:
            raise HTTPException(404, {"code": "unknown_report"}) from exc

    @app.get("/reports/{report_id}/download")
    def download(report_id: str):
        try:
            return reports.download(report_id)
        except UnknownReport as exc:
            raise HTTPException(404, {"code": "unknown_report"}) from exc
        except NotReady as exc:
            raise HTTPException(409, {"code": "not_ready"}) from exc

    return app


app = create_app()
