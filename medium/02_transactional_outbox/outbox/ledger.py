import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Ledger:
    def __init__(self, path: str):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id TEXT PRIMARY KEY,
                customer TEXT NOT NULL,
                sku TEXT NOT NULL,
                total INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS outbox (
                id TEXT PRIMARY KEY,
                order_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                payload TEXT NOT NULL,
                published INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS invoices (
                id TEXT PRIMARY KEY,
                message_id TEXT NOT NULL UNIQUE,
                order_id TEXT NOT NULL,
                total INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS inbox (
                message_id TEXT PRIMARY KEY,
                accepted_at TEXT NOT NULL
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

    def place(self, customer: str, sku: str, total: int) -> dict:
        order_id = uuid.uuid4().hex
        message_id = uuid.uuid4().hex
        payload = json.dumps(
            {"order_id": order_id, "customer": customer, "sku": sku, "total": total},
            ensure_ascii=False,
        )
        with self.transaction():
            self.conn.execute(
                "INSERT INTO orders (id, customer, sku, total) VALUES (?, ?, ?, ?)",
                (order_id, customer, sku, total),
            )
            self.conn.execute(
                """
                INSERT INTO outbox (id, order_id, event_type, payload)
                VALUES (?, ?, 'order.placed', ?)
                """,
                (message_id, order_id, payload),
            )
        return {"order_id": order_id, "message_id": message_id}

    def order(self, order_id: str):
        return self.conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()

    def pending(self):
        rows = self.conn.execute(
            "SELECT * FROM outbox WHERE published = 0 ORDER BY id"
        ).fetchall()
        return [self._message(row) for row in rows]

    def accept(self, message_id: str, event_type: str, payload: dict) -> str:
        with self.transaction():
            seen = self.conn.execute(
                "SELECT message_id FROM inbox WHERE message_id = ?",
                (message_id,),
            ).fetchone()
            if seen is not None:
                return "duplicate"
            self.conn.execute(
                "INSERT INTO invoices (id, message_id, order_id, total) VALUES (?, ?, ?, ?)",
                (uuid.uuid4().hex, message_id, payload["order_id"], payload["total"]),
            )
            self.conn.execute(
                "INSERT INTO inbox (message_id, accepted_at) VALUES (?, ?)",
                (message_id, now()),
            )
            self.conn.execute(
                "UPDATE outbox SET published = 1 WHERE id = ?",
                (message_id,),
            )
        return "accepted" if event_type else "accepted"

    def relay(self) -> list[str]:
        delivered = []
        for message in self.pending():
            self.accept(message["id"], message["event_type"], message["payload"])
            delivered.append(message["id"])
        return delivered

    def invoices(self):
        return [dict(row) for row in self.conn.execute("SELECT * FROM invoices ORDER BY id")]

    def _message(self, row) -> dict:
        return {
            "id": row["id"],
            "order_id": row["order_id"],
            "event_type": row["event_type"],
            "payload": json.loads(row["payload"]),
            "published": bool(row["published"]),
        }
