import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from otp.service import AuthError, TwoFactor, totp
import base64


class UserIn(BaseModel):
    email: str
    password: str = Field(min_length=8)


class CodeIn(BaseModel):
    code: str


class LoginIn(BaseModel):
    email: str
    password: str
    code: str


def create_app(database: str | None = None) -> FastAPI:
    auth = TwoFactor(database or os.environ.get("DATABASE_PATH", ":memory:"))
    app = FastAPI(title="Two Factor")
    app.state.auth = auth

    def guard(call):
        try:
            return call()
        except AuthError as exc:
            raise HTTPException(exc.status, {"code": exc.code}) from exc

    @app.post("/users", status_code=201)
    def users(body: UserIn):
        return auth.register(body.email, body.password)

    @app.post("/users/{user_id}/enroll")
    def enroll(user_id: str):
        return guard(lambda: auth.enroll(user_id))

    @app.post("/users/{user_id}/confirm")
    def confirm(user_id: str, body: CodeIn):
        return guard(lambda: auth.confirm(user_id, body.code))

    @app.post("/login")
    def login(body: LoginIn):
        return guard(lambda: auth.login(body.email, body.password, body.code))

    @app.get("/users/{user_id}/current-code")
    def current_code(user_id: str):
        user = auth._require(user_id)
        padded = user["totp_secret"] + "=" * ((8 - len(user["totp_secret"]) % 8) % 8)
        secret = base64.b32decode(padded)
        return {"code": totp(secret, auth.now)}

    return app


app = create_app()
