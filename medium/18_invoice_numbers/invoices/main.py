import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


class IssueIn(BaseModel):
    customer: str
    total: int = Field(gt=0)


def create_app(database: str | None = None) -> FastAPI:
    from invoices.service import Invoices, UnknownInvoice

    book = Invoices(database or os.environ.get("DATABASE_PATH", ":memory:"))
    app = FastAPI(title="Invoice Numbers")

    @app.post("/invoices", status_code=201)
    def issue(body: IssueIn):
        return book.issue(body.customer, body.total)

    @app.post("/invoices/{number}/void")
    def void(number: str):
        try:
            return book.void(number)
        except UnknownInvoice as exc:
            raise HTTPException(404, {"code": "unknown_invoice"}) from exc

    return app


app = create_app()
