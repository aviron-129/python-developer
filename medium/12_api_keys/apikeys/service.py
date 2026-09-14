import hashlib
import secrets
import sqlite3
import uuid
from contextlib import contextmanager


class UnknownKey(Exception):
    pass


class Forbidden(Exception):
    pass


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


class KeyStore:
    def __init__(self, path: str):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS keys (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                prefix TEXT NOT NULL UNIQUE,
                secret_hash TEXT NOT NULL,
                scopes TEXT NOT NULL,
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

    def issue(self, name: str, scopes: list[str]) -> dict:
        key_id = uuid.uuid4().hex
        prefix = "pk_" + secrets.token_hex(4)
        secret = secrets.token_urlsafe(24)
        token = f"{prefix}.{secret}"
        with self.transaction():
            self.conn.execute(
                "INSERT INTO keys (id, name, prefix, secret_hash, scopes) VALUES (?, ?, ?, ?, ?)",
                (key_id, name, prefix, digest(secret), " ".join(scopes)),
            )
        payload = self.public(key_id)
        payload["token"] = token
        return payload

    def rotate(self, key_id: str) -> dict:
        self.public(key_id)
        secret = secrets.token_urlsafe(24)
        row = self.conn.execute("SELECT prefix FROM keys WHERE id = ?", (key_id,)).fetchone()
        with self.transaction():
            self.conn.execute(
                "UPDATE keys SET secret_hash = ?, revoked = 0 WHERE id = ?",
                (digest(secret), key_id),
            )
        payload = self.public(key_id)
        payload["token"] = f"{row['prefix']}.{secret}"
        return payload

    def revoke(self, key_id: str) -> dict:
        self.public(key_id)
        with self.transaction():
            self.conn.execute("UPDATE keys SET revoked = 1 WHERE id = ?", (key_id,))
        return self.public(key_id)

    def authorize(self, token: str, scope: str) -> dict:
        prefix, _, secret = token.partition(".")
        row = self.conn.execute("SELECT * FROM keys WHERE prefix = ?", (prefix,)).fetchone()
        if row is None or row["revoked"] or not secret or digest(secret) != row["secret_hash"]:
            raise Forbidden()
        if scope not in row["scopes"].split():
            raise Forbidden()
        return {"key_id": row["id"], "scope": scope}

    def public(self, key_id: str) -> dict:
        row = self.conn.execute("SELECT id, name, prefix, scopes, revoked FROM keys WHERE id = ?", (key_id,)).fetchone()
        if row is None:
            raise UnknownKey()
        payload = dict(row)
        payload["scopes"] = payload["scopes"].split()
        payload["revoked"] = bool(payload["revoked"])
        return payload
