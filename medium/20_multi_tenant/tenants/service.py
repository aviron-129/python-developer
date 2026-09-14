import sqlite3
import uuid
from contextlib import contextmanager


class MissingTenant(Exception):
    pass


class UnknownNote(Exception):
    pass


class Notes:
    def __init__(self, path: str):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS notes (
                id TEXT PRIMARY KEY,
                tenant TEXT NOT NULL,
                body TEXT NOT NULL
            )
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

    def add(self, tenant: str, body: str) -> dict:
        self._require(tenant)
        note_id = uuid.uuid4().hex
        with self.transaction():
            self.conn.execute(
                "INSERT INTO notes (id, tenant, body) VALUES (?, ?, ?)",
                (note_id, tenant, body),
            )
        return {"id": note_id, "tenant": tenant, "body": body}

    def list_for(self, tenant: str) -> list[dict]:
        self._require(tenant)
        rows = self.conn.execute("SELECT id, body FROM notes WHERE tenant = ? ORDER BY body", (tenant,))
        return [dict(row) for row in rows]

    def read(self, tenant: str, note_id: str) -> dict:
        self._require(tenant)
        row = self.conn.execute(
            "SELECT id, body FROM notes WHERE id = ? AND tenant = ?",
            (note_id, tenant),
        ).fetchone()
        if row is None:
            raise UnknownNote()
        return dict(row)

    def _require(self, tenant: str) -> None:
        if not tenant:
            raise MissingTenant()
