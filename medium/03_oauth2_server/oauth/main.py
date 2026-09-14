import os

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from oauth.domain import AuthError
from oauth.server import AuthServer, Clock


class UserIn(BaseModel):
    email: str
    password: str = Field(min_length=8)


class ClientIn(BaseModel):
    name: str
    redirect_uri: str


class AuthorizeIn(BaseModel):
    email: str
    password: str
    client_id: str
    redirect_uri: str
    scope: str = "profile"


class TokenIn(BaseModel):
    grant_type: str
    client_id: str
    client_secret: str
    code: str | None = None
    redirect_uri: str | None = None
    refresh_token: str | None = None


class RevokeIn(BaseModel):
    token: str
    client_id: str
    client_secret: str


class AdvanceIn(BaseModel):
    seconds: int = Field(gt=0)


def create_app(database: str | None = None, clock: Clock | None = None) -> FastAPI:
    auth = AuthServer(database or os.environ.get("DATABASE_PATH", ":memory:"), clock)
    app = FastAPI(title="OAuth2 Authorization Server")
    app.state.auth = auth

    def guard(call):
        try:
            return call()
        except AuthError as exc:
            raise HTTPException(exc.status, {"code": exc.code}) from exc

    @app.post("/users", status_code=201)
    def users(body: UserIn):
        return guard(lambda: auth.register_user(body.email, body.password))

    @app.post("/clients", status_code=201)
    def clients(body: ClientIn):
        return auth.register_client(body.name, body.redirect_uri)

    @app.post("/oauth/authorize")
    def authorize(body: AuthorizeIn):
        return guard(
            lambda: auth.authorize(
                body.email, body.password, body.client_id, body.redirect_uri, body.scope
            )
        )

    @app.post("/oauth/token")
    def token(body: TokenIn):
        if body.grant_type == "authorization_code":
            return guard(
                lambda: auth.exchange_code(
                    body.code or "", body.client_id, body.client_secret, body.redirect_uri or ""
                )
            )
        if body.grant_type == "refresh_token":
            return guard(
                lambda: auth.refresh(body.refresh_token or "", body.client_id, body.client_secret)
            )
        raise HTTPException(400, {"code": "unsupported_grant"})

    @app.get("/userinfo")
    def userinfo(authorization: str = Header(default="")):
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token:
            raise HTTPException(401, {"code": "invalid_token"})
        return guard(lambda: auth.userinfo(token))

    @app.post("/oauth/revoke", status_code=200)
    def revoke(body: RevokeIn):
        return guard(lambda: auth.revoke(body.token, body.client_id, body.client_secret) or {"revoked": True})

    @app.post("/clock")
    def clock_shift(body: AdvanceIn):
        auth.clock.advance(body.seconds)
        return {"now": auth.clock.now.isoformat()}

    return app


app = create_app()
