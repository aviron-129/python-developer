import json
import sqlite3
import uuid
from contextlib import contextmanager


class Queue:
    def __init__(self, path: str):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                attempts INTEGER NOT NULL,
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

    def enqueue(self, payload: dict) -> dict:
        job_id = uuid.uuid4().hex
        with self.transaction():
            self.conn.execute(
                "INSERT INTO jobs (id, payload, attempts, status) VALUES (?, ?, 0, 'queued')",
                (job_id, json.dumps(payload)),
            )
        return self.get(job_id)

    def work(self, limit: int = 10) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM jobs WHERE status = 'queued' ORDER BY id LIMIT ?",
            (limit,),
        ).fetchall()
        done = []
        for row in rows:
            payload = json.loads(row["payload"])
            attempts = row["attempts"] + 1
            fail = bool(payload.get("fail")) and attempts < int(payload.get("succeed_on", 99))
            if fail and attempts >= 3:
                status = "dead"
            elif fail:
                status = "queued"
            else:
                status = "done"
                payload["fail"] = False
            with self.transaction():
                self.conn.execute(
                    "UPDATE jobs SET attempts = ?, status = ?, payload = ? WHERE id = ?",
                    (attempts, status, json.dumps(payload), row["id"]),
                )
            done.append(self.get(row["id"]))
        return done

    def dead(self) -> list[dict]:
        rows = self.conn.execute("SELECT * FROM jobs WHERE status = 'dead' ORDER BY id")
        return [self._public(row) for row in rows]

    def replay(self, job_id: str) -> dict:
        row = self.conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        payload = json.loads(row["payload"])
        payload["fail"] = False
        with self.transaction():
            self.conn.execute(
                "UPDATE jobs SET status = 'queued', payload = ? WHERE id = ?",
                (json.dumps(payload), job_id),
            )
        return self.get(job_id)

    def get(self, job_id: str) -> dict:
        row = self.conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        return self._public(row)

    def _public(self, row) -> dict:
        return {
            "id": row["id"],
            "attempts": row["attempts"],
            "status": row["status"],
            "payload": json.loads(row["payload"]),
        }
