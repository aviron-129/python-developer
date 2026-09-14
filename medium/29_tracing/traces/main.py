from fastapi import FastAPI
from pydantic import BaseModel, Field


class OrderIn(BaseModel):
    sku: str
    qty: int = Field(gt=0)
    stock: int = Field(ge=0)


def create_app() -> FastAPI:
    from traces.service import TraceBook

    book = TraceBook()
    app = FastAPI(title="Tracing")
    app.state.book = book

    @app.post("/orders", status_code=201)
    def place(body: OrderIn):
        return book.place_order(body.sku, body.qty, body.stock)

    @app.get("/traces/{trace_id}")
    def read(trace_id: str):
        return book.read(trace_id)

    return app


app = create_app()
