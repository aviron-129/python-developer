import sqlite3
import uuid
from contextlib import contextmanager


class UnknownUpload(Exception):
    pass


class Uploads:
    def __init__(self, path: str):
        self.blobs: dict[str, bytes] = {}
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS uploads (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                status TEXT NOT NULL,
                detail TEXT
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

    def intent(self, filename: str) -> dict:
        upload_id = uuid.uuid4().hex
        with self.transaction():
            self.conn.execute(
                "INSERT INTO uploads (id, filename, status) VALUES (?, ?, 'pending')",
                (upload_id, filename),
            )
        return {"id": upload_id, "token": upload_id, "status": "pending"}

    def store(self, upload_id: str, content: bytes) -> dict:
        self.get(upload_id)
        self.blobs[upload_id] = content
        with self.transaction():
            self.conn.execute("UPDATE uploads SET status = 'stored' WHERE id = ?", (upload_id,))
        return self.get(upload_id)

    def process(self, upload_id: str) -> dict:
        row = self.get(upload_id)
        content = self.blobs.get(upload_id, b"")
        if not content.startswith(b"\x89PNG") or len(content) > 20:
            status, detail = "rejected", "not_a_small_png"
        else:
            status, detail = "ready", f"preview:{len(content)}"
        with self.transaction():
            self.conn.execute(
                "UPDATE uploads SET status = ?, detail = ? WHERE id = ?",
                (status, detail, upload_id),
            )
        return self.get(row["id"])

    def get(self, upload_id: str) -> dict:
        row = self.conn.execute("SELECT * FROM uploads WHERE id = ?", (upload_id,)).fetchone()
        if row is None:
            raise UnknownUpload()
        return dict(row)
