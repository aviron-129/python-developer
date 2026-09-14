import hashlib
import hmac
import json
import sqlite3
import uuid
from contextlib import contextmanager


def sign(secret: str, body: str) -> str:
    return hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()


class Dispatcher:
    def __init__(self, path: str):
        self.sinks: dict[str, dict] = {}
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS subscriptions (
                id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                target TEXT NOT NULL,
                secret TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS deliveries (
                id TEXT PRIMARY KEY,
                subscription_id TEXT NOT NULL,
                attempt INTEGER NOT NULL,
                status TEXT NOT NULL,
                signature TEXT NOT NULL
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

    def subscribe(self, event_type: str, target: str, secret: str, fail_times: int) -> dict:
        sub_id = uuid.uuid4().hex
        self.sinks[target] = {"fail_times": fail_times, "seen": []}
        with self.transaction():
            self.conn.execute(
                "INSERT INTO subscriptions (id, event_type, target, secret) VALUES (?, ?, ?, ?)",
                (sub_id, event_type, target, secret),
            )
        return {"id": sub_id, "event_type": event_type, "target": target}

    def emit(self, event_type: str, payload: dict, max_attempts: int = 3) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM subscriptions WHERE event_type = ?",
            (event_type,),
        ).fetchall()
        results = []
        body = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        for row in rows:
            results.append(self._deliver(row, body, max_attempts))
        return results

    def _deliver(self, row, body: str, max_attempts: int) -> dict:
        sink = self.sinks[row["target"]]
        signature = sign(row["secret"], body)
        for attempt in range(1, max_attempts + 1):
            if sink["fail_times"] > 0:
                sink["fail_times"] -= 1
                status = "failed"
            else:
                sink["seen"].append({"body": body, "signature": signature})
                status = "delivered"
            with self.transaction():
                self.conn.execute(
                    """
                    INSERT INTO deliveries (id, subscription_id, attempt, status, signature)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (uuid.uuid4().hex, row["id"], attempt, status, signature),
                )
            if status == "delivered":
                return {"target": row["target"], "attempts": attempt, "status": "delivered"}
        return {"target": row["target"], "attempts": max_attempts, "status": "failed"}
