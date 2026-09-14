from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from breaker.domain import CircuitOpen, UpstreamDown
from breaker.machine import Breaker, Clock


class ModeIn(BaseModel):
    fail: bool
    body: dict = Field(default_factory=dict)


class CallIn(BaseModel):
    service: str = Field(min_length=1)


class AdvanceIn(BaseModel):
    seconds: float = Field(gt=0)


def create_app() -> FastAPI:
    clock = Clock()
    breaker = Breaker(clock)
    upstreams: dict[str, dict] = {}
    app = FastAPI(title="Circuit Breaker")
    app.state.breaker = breaker
    app.state.clock = clock
    app.state.upstreams = upstreams

    @app.put("/upstreams/{name}")
    def set_mode(name: str, body: ModeIn):
        slot = upstreams.setdefault(name, {"fail": False, "body": {}, "calls": 0})
        slot["fail"] = body.fail
        slot["body"] = body.body
        return {"name": name, "fail": body.fail, "calls": slot["calls"]}

    @app.post("/calls")
    def call(body: CallIn):
        slot = upstreams.setdefault(body.service, {"fail": True, "body": {}, "calls": 0})

        def operation():
            slot["calls"] += 1
            if slot["fail"]:
                raise UpstreamDown()
            return slot["body"]

        try:
            result = breaker.call(body.service, operation)
        except CircuitOpen:
            raise HTTPException(503, {"code": "circuit_open", "service": body.service}) from None
        except UpstreamDown:
            raise HTTPException(502, {"code": "upstream_down", "service": body.service}) from None
        return {**result, "calls": slot["calls"]}

    @app.get("/circuits/{name}")
    def circuit(name: str):
        return breaker.snapshot(name)

    @app.post("/circuits/{name}/reset")
    def reset(name: str):
        return breaker.reset(name)

    @app.post("/clock")
    def clock_shift(body: AdvanceIn):
        clock.advance(body.seconds)
        return {"now": clock.now}

    return app


app = create_app()
