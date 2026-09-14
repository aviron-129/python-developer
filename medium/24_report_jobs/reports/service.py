import sqlite3
import uuid
from contextlib import contextmanager


class UnknownReport(Exception):
    pass


class NotReady(Exception):
    pass


class Reports:
    def __init__(self, path: str):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY,
                start_on TEXT NOT NULL,
                end_on TEXT NOT NULL,
                progress INTEGER NOT NULL,
                status TEXT NOT NULL,
                body TEXT
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

    def start(self, start_on: str, end_on: str) -> dict:
        report_id = uuid.uuid4().hex
        if end_on < start_on:
            status, progress, body = "failed", 0, None
        else:
            status, progress, body = "running", 0, None
        with self.transaction():
            self.conn.execute(
                """
                INSERT INTO reports (id, start_on, end_on, progress, status, body)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (report_id, start_on, end_on, progress, status, body),
            )
        return self.get(report_id)

    def tick(self, report_id: str) -> dict:
        row = self._row(report_id)
        if row["status"] != "running":
            return dict(row)
        progress = min(row["progress"] + 50, 100)
        status = "ready" if progress == 100 else "running"
        body = f"{row['start_on']}..{row['end_on']}" if status == "ready" else None
        with self.transaction():
            self.conn.execute(
                "UPDATE reports SET progress = ?, status = ?, body = ? WHERE id = ?",
                (progress, status, body, report_id),
            )
        return self.get(report_id)

    def download(self, report_id: str) -> dict:
        row = self.get(report_id)
        if row["status"] != "ready":
            raise NotReady()
        return {"id": report_id, "body": row["body"]}

    def get(self, report_id: str) -> dict:
        return dict(self._row(report_id))

    def _row(self, report_id: str):
        row = self.conn.execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()
        if row is None:
            raise UnknownReport()
        return row
