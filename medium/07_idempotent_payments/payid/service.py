import hashlib
import json
import sqlite3
import uuid
from contextlib import contextmanager


class Conflict(Exception):
    pass


class UnknownPayment(Exception):
    pass


class AlreadyRefunded(Exception):
    pass


def fingerprint(body: dict) -> str:
    raw = json.dumps(body, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode()).hexdigest()


class Payments:
    def __init__(self, path: str):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS payments (
                id TEXT PRIMARY KEY,
                amount INTEGER NOT NULL,
                currency TEXT NOT NULL,
                status TEXT NOT NULL,
                idem_key TEXT NOT NULL UNIQUE,
                request_hash TEXT NOT NULL
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

    def charge(self, key: str, amount: int, currency: str) -> tuple[dict, bool]:
        body_hash = fingerprint({"amount": amount, "currency": currency})
        with self.transaction():
            existing = self.conn.execute(
                "SELECT * FROM payments WHERE idem_key = ?",
                (key,),
            ).fetchone()
            if existing is not None:
                if existing["request_hash"] != body_hash:
                    raise Conflict()
                return dict(existing), True
            payment_id = uuid.uuid4().hex
            self.conn.execute(
                """
                INSERT INTO payments (id, amount, currency, status, idem_key, request_hash)
                VALUES (?, ?, ?, 'captured', ?, ?)
                """,
                (payment_id, amount, currency, key, body_hash),
            )
        return self.get(payment_id), False

    def refund(self, payment_id: str) -> dict:
        with self.transaction():
            row = self.conn.execute("SELECT * FROM payments WHERE id = ?", (payment_id,)).fetchone()
            if row is None:
                raise UnknownPayment()
            if row["status"] == "refunded":
                raise AlreadyRefunded()
            self.conn.execute(
                "UPDATE payments SET status = 'refunded' WHERE id = ?",
                (payment_id,),
            )
        return self.get(payment_id)

    def get(self, payment_id: str) -> dict:
        row = self.conn.execute("SELECT * FROM payments WHERE id = ?", (payment_id,)).fetchone()
        if row is None:
            raise UnknownPayment()
        return dict(row)
