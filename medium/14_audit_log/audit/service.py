import hashlib
import json
import sqlite3
import uuid
from contextlib import contextmanager


class BrokenChain(Exception):
    pass


def link(prev: str, payload: dict) -> str:
    raw = prev + json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode()).hexdigest()


class AuditLog:
    def __init__(self, path: str):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                seq INTEGER NOT NULL UNIQUE,
                actor TEXT NOT NULL,
                action TEXT NOT NULL,
                subject TEXT NOT NULL,
                at TEXT NOT NULL,
                prev_hash TEXT NOT NULL,
                event_hash TEXT NOT NULL
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

    def append(self, actor: str, action: str, subject: str, at: str) -> dict:
        with self.transaction():
            last = self.conn.execute("SELECT seq, event_hash FROM events ORDER BY seq DESC LIMIT 1").fetchone()
            seq = 1 if last is None else last["seq"] + 1
            prev = "genesis" if last is None else last["event_hash"]
            payload = {"seq": seq, "actor": actor, "action": action, "subject": subject, "at": at}
            event_hash = link(prev, payload)
            event_id = uuid.uuid4().hex
            self.conn.execute(
                """
                INSERT INTO events (id, seq, actor, action, subject, at, prev_hash, event_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (event_id, seq, actor, action, subject, at, prev, event_hash),
            )
        return self._public(self.conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone())

    def query(self, actor: str | None, action: str | None) -> list[dict]:
        sql = "SELECT * FROM events WHERE 1 = 1"
        params: list[str] = []
        if actor:
            sql += " AND actor = ?"
            params.append(actor)
        if action:
            sql += " AND action = ?"
            params.append(action)
        sql += " ORDER BY seq"
        return [self._public(row) for row in self.conn.execute(sql, params)]

    def verify(self) -> dict:
        prev = "genesis"
        for row in self.conn.execute("SELECT * FROM events ORDER BY seq"):
            payload = {
                "seq": row["seq"],
                "actor": row["actor"],
                "action": row["action"],
                "subject": row["subject"],
                "at": row["at"],
            }
            expected = link(prev, payload)
            if row["prev_hash"] != prev or row["event_hash"] != expected:
                raise BrokenChain()
            prev = row["event_hash"]
        count = self.conn.execute("SELECT COUNT(*) AS n FROM events").fetchone()["n"]
        return {"ok": True, "events": count}

    def _public(self, row) -> dict:
        return {
            "id": row["id"],
            "seq": row["seq"],
            "actor": row["actor"],
            "action": row["action"],
            "subject": row["subject"],
            "at": row["at"],
        }
