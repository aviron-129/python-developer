import hashlib
import secrets
import sqlite3
import uuid
from contextlib import contextmanager


class UnknownSession(Exception):
    pass


def digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class Sessions:
    def __init__(self, path: str):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                device TEXT NOT NULL,
                token_hash TEXT NOT NULL UNIQUE,
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

    def login(self, user_id: str, device: str) -> dict:
        session_id = uuid.uuid4().hex
        token = secrets.token_urlsafe(24)
        with self.transaction():
            self.conn.execute(
                "INSERT INTO sessions (id, user_id, device, token_hash) VALUES (?, ?, ?, ?)",
                (session_id, user_id, device, digest(token)),
            )
        payload = self._public(session_id)
        payload["token"] = token
        return payload

    def list_for(self, user_id: str) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM sessions WHERE user_id = ? ORDER BY device",
            (user_id,),
        )
        return [self._public_row(row) for row in rows]

    def revoke(self, session_id: str) -> dict:
        if self.conn.execute("SELECT id FROM sessions WHERE id = ?", (session_id,)).fetchone() is None:
            raise UnknownSession()
        with self.transaction():
            self.conn.execute("UPDATE sessions SET revoked = 1 WHERE id = ?", (session_id,))
        return self._public(session_id)

    def revoke_all(self, user_id: str) -> dict:
        with self.transaction():
            cur = self.conn.execute("UPDATE sessions SET revoked = 1 WHERE user_id = ?", (user_id,))
        return {"revoked": cur.rowcount}

    def me(self, token: str) -> dict:
        row = self.conn.execute("SELECT * FROM sessions WHERE token_hash = ?", (digest(token),)).fetchone()
        if row is None or row["revoked"]:
            raise UnknownSession()
        return self._public_row(row)

    def _public(self, session_id: str) -> dict:
        row = self.conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
        return self._public_row(row)

    def _public_row(self, row) -> dict:
        return {
            "id": row["id"],
            "user_id": row["user_id"],
            "device": row["device"],
            "revoked": bool(row["revoked"]),
        }
