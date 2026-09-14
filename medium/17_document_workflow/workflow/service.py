import sqlite3
import uuid
from contextlib import contextmanager


TRANSITIONS = {
    ("draft", "submit"): "in_review",
    ("in_review", "approve"): "approved",
    ("in_review", "reject"): "draft",
    ("approved", "publish"): "published",
}


class WorkflowError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


class Documents:
    def __init__(self, path: str):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                status TEXT NOT NULL
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

    def create(self, title: str, author: str) -> dict:
        doc_id = uuid.uuid4().hex
        with self.transaction():
            self.conn.execute(
                "INSERT INTO documents (id, title, author, status) VALUES (?, ?, ?, 'draft')",
                (doc_id, title, author),
            )
        return self.get(doc_id)

    def act(self, doc_id: str, action: str, actor: str) -> dict:
        row = self._row(doc_id)
        nxt = TRANSITIONS.get((row["status"], action))
        if nxt is None:
            raise WorkflowError("illegal_transition")
        if action == "approve" and actor == row["author"]:
            raise WorkflowError("author_cannot_approve")
        with self.transaction():
            self.conn.execute("UPDATE documents SET status = ? WHERE id = ?", (nxt, doc_id))
        return self.get(doc_id)

    def get(self, doc_id: str) -> dict:
        return dict(self._row(doc_id))

    def _row(self, doc_id: str):
        row = self.conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
        if row is None:
            raise WorkflowError("unknown_document")
        return row
