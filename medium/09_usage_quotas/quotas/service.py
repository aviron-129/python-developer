import sqlite3
import uuid
from contextlib import contextmanager


class UnknownAccount(Exception):
    pass


class QuotaExceeded(Exception):
    def __init__(self, used: int, limit: int, requested: int):
        self.used = used
        self.limit = limit
        self.requested = requested
        super().__init__("quota")


class Quotas:
    def __init__(self, path: str):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS accounts (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                monthly_limit INTEGER NOT NULL,
                used INTEGER NOT NULL,
                period INTEGER NOT NULL
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

    def open_account(self, name: str, monthly_limit: int) -> dict:
        account_id = uuid.uuid4().hex
        with self.transaction():
            self.conn.execute(
                """
                INSERT INTO accounts (id, name, monthly_limit, used, period)
                VALUES (?, ?, ?, 0, 1)
                """,
                (account_id, name, monthly_limit),
            )
        return self.get(account_id)

    def consume(self, account_id: str, units: int) -> dict:
        with self.transaction():
            row = self._row(account_id)
            if row["used"] + units > row["monthly_limit"]:
                raise QuotaExceeded(row["used"], row["monthly_limit"], units)
            self.conn.execute(
                "UPDATE accounts SET used = used + ? WHERE id = ?",
                (units, account_id),
            )
        return self.get(account_id)

    def close_period(self, account_id: str) -> dict:
        self.get(account_id)
        with self.transaction():
            self.conn.execute(
                "UPDATE accounts SET used = 0, period = period + 1 WHERE id = ?",
                (account_id,),
            )
        return self.get(account_id)

    def get(self, account_id: str) -> dict:
        row = self._row(account_id)
        payload = dict(row)
        payload["remaining"] = payload["monthly_limit"] - payload["used"]
        return payload

    def _row(self, account_id: str):
        row = self.conn.execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone()
        if row is None:
            raise UnknownAccount()
        return row
