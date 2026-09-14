import hashlib
import hmac
import secrets
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

from oauth.domain import AuthError


def hash_secret(value: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", value.encode(), salt, 20_000)
    return f"{salt.hex()}${digest.hex()}"


def check_secret(value: str, stored: str) -> bool:
    salt_hex, _digest = stored.split("$", 1)
    candidate = hash_secret(value, bytes.fromhex(salt_hex))
    return hmac.compare_digest(candidate, stored)


def digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class Clock:
    def __init__(self):
        self.now = datetime(2026, 9, 14, 12, 0, tzinfo=timezone.utc)

    def advance(self, seconds: int) -> None:
        self.now += timedelta(seconds=seconds)


class AuthServer:
    def __init__(self, path: str, clock: Clock | None = None):
        self.clock = clock or Clock()
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS clients (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                secret_hash TEXT NOT NULL,
                redirect_uri TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS codes (
                code_hash TEXT PRIMARY KEY,
                client_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                redirect_uri TEXT NOT NULL,
                scope TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                used INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS tokens (
                token_hash TEXT PRIMARY KEY,
                kind TEXT NOT NULL,
                client_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                family_id TEXT NOT NULL,
                scope TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                revoked INTEGER NOT NULL DEFAULT 0
            );
            """
        )
        self.conn.commit()

    @contextmanager
    def transaction(self):
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            yield
        except Exception:
            self.conn.rollback()
            raise
        else:
            self.conn.commit()

    def register_user(self, email: str, password: str) -> dict:
        email = email.strip().lower()
        user_id = uuid.uuid4().hex
        with self.transaction():
            exists = self.conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
            if exists is not None:
                raise AuthError("email_taken", 409)
            self.conn.execute(
                "INSERT INTO users (id, email, password_hash) VALUES (?, ?, ?)",
                (user_id, email, hash_secret(password)),
            )
        return {"id": user_id, "email": email}

    def register_client(self, name: str, redirect_uri: str) -> dict:
        client_id = uuid.uuid4().hex
        secret = secrets.token_urlsafe(24)
        with self.transaction():
            self.conn.execute(
                "INSERT INTO clients (id, name, secret_hash, redirect_uri) VALUES (?, ?, ?, ?)",
                (client_id, name, hash_secret(secret), redirect_uri),
            )
        return {"client_id": client_id, "client_secret": secret, "redirect_uri": redirect_uri}

    def authorize(self, email: str, password: str, client_id: str, redirect_uri: str, scope: str) -> dict:
        user = self._user_by_password(email, password)
        client = self._client(client_id)
        if client["redirect_uri"] != redirect_uri:
            raise AuthError("redirect_mismatch", 400)
        code = secrets.token_urlsafe(24)
        expires = (self.clock.now + timedelta(seconds=120)).isoformat()
        with self.transaction():
            self.conn.execute(
                """
                INSERT INTO codes (code_hash, client_id, user_id, redirect_uri, scope, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (digest(code), client_id, user["id"], redirect_uri, scope, expires),
            )
        return {"code": code, "expires_in": 120}

    def exchange_code(self, code: str, client_id: str, client_secret: str, redirect_uri: str) -> dict:
        self._check_client(client_id, client_secret)
        row = self.conn.execute(
            "SELECT * FROM codes WHERE code_hash = ?",
            (digest(code),),
        ).fetchone()
        if row is None or row["used"] or row["client_id"] != client_id or row["redirect_uri"] != redirect_uri:
            raise AuthError("invalid_code", 400)
        if row["expires_at"] <= self.clock.now.isoformat():
            raise AuthError("code_expired", 400)
        with self.transaction():
            self.conn.execute("UPDATE codes SET used = 1 WHERE code_hash = ?", (digest(code),))
        return self._issue(row["client_id"], row["user_id"], row["scope"], uuid.uuid4().hex)

    def refresh(self, refresh_token: str, client_id: str, client_secret: str) -> dict:
        self._check_client(client_id, client_secret)
        row = self.conn.execute(
            "SELECT * FROM tokens WHERE token_hash = ? AND kind = 'refresh'",
            (digest(refresh_token),),
        ).fetchone()
        if row is None or row["client_id"] != client_id:
            raise AuthError("invalid_grant", 400)
        if row["revoked"]:
            self._revoke_family(row["family_id"])
            raise AuthError("refresh_reused", 400)
        if row["expires_at"] <= self.clock.now.isoformat():
            raise AuthError("refresh_expired", 400)
        with self.transaction():
            self.conn.execute(
                "UPDATE tokens SET revoked = 1 WHERE token_hash = ?",
                (digest(refresh_token),),
            )
        return self._issue(row["client_id"], row["user_id"], row["scope"], row["family_id"])

    def userinfo(self, access_token: str) -> dict:
        row = self.conn.execute(
            "SELECT * FROM tokens WHERE token_hash = ? AND kind = 'access'",
            (digest(access_token),),
        ).fetchone()
        if row is None or row["revoked"] or row["expires_at"] <= self.clock.now.isoformat():
            raise AuthError("invalid_token", 401)
        if "profile" not in row["scope"].split():
            raise AuthError("insufficient_scope", 403)
        user = self.conn.execute("SELECT id, email FROM users WHERE id = ?", (row["user_id"],)).fetchone()
        return {"sub": user["id"], "email": user["email"], "scope": row["scope"]}

    def revoke(self, token: str, client_id: str, client_secret: str) -> None:
        self._check_client(client_id, client_secret)
        row = self.conn.execute(
            "SELECT family_id FROM tokens WHERE token_hash = ? AND client_id = ?",
            (digest(token), client_id),
        ).fetchone()
        if row is None:
            return
        self._revoke_family(row["family_id"])

    def _issue(self, client_id: str, user_id: str, scope: str, family_id: str) -> dict:
        access = secrets.token_urlsafe(32)
        refresh = secrets.token_urlsafe(32)
        access_exp = (self.clock.now + timedelta(minutes=15)).isoformat()
        refresh_exp = (self.clock.now + timedelta(days=14)).isoformat()
        with self.transaction():
            self.conn.execute(
                """
                INSERT INTO tokens (token_hash, kind, client_id, user_id, family_id, scope, expires_at)
                VALUES (?, 'access', ?, ?, ?, ?, ?)
                """,
                (digest(access), client_id, user_id, family_id, scope, access_exp),
            )
            self.conn.execute(
                """
                INSERT INTO tokens (token_hash, kind, client_id, user_id, family_id, scope, expires_at)
                VALUES (?, 'refresh', ?, ?, ?, ?, ?)
                """,
                (digest(refresh), client_id, user_id, family_id, scope, refresh_exp),
            )
        return {
            "access_token": access,
            "refresh_token": refresh,
            "token_type": "bearer",
            "expires_in": 900,
            "scope": scope,
        }

    def _revoke_family(self, family_id: str) -> None:
        with self.transaction():
            self.conn.execute("UPDATE tokens SET revoked = 1 WHERE family_id = ?", (family_id,))

    def _user_by_password(self, email: str, password: str):
        row = self.conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email.strip().lower(),),
        ).fetchone()
        if row is None or not check_secret(password, row["password_hash"]):
            raise AuthError("invalid_credentials", 401)
        return row

    def _client(self, client_id: str):
        row = self.conn.execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone()
        if row is None:
            raise AuthError("unknown_client", 401)
        return row

    def _check_client(self, client_id: str, client_secret: str) -> None:
        client = self._client(client_id)
        if not check_secret(client_secret, client["secret_hash"]):
            raise AuthError("invalid_client", 401)
