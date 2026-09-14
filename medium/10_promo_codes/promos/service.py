import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone


class PromoError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


class Promos:
    def __init__(self, path: str):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS codes (
                code TEXT PRIMARY KEY,
                kind TEXT NOT NULL,
                value INTEGER NOT NULL,
                max_uses INTEGER NOT NULL,
                used INTEGER NOT NULL,
                expires_on TEXT NOT NULL,
                referrer TEXT
            );
            CREATE TABLE IF NOT EXISTS redemptions (
                code TEXT NOT NULL,
                user_id TEXT NOT NULL,
                discount INTEGER NOT NULL,
                PRIMARY KEY (code, user_id)
            );
            CREATE TABLE IF NOT EXISTS credits (
                user_id TEXT PRIMARY KEY,
                amount INTEGER NOT NULL
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

    def create(self, code: str, kind: str, value: int, max_uses: int, expires_on: str, referrer: str | None) -> dict:
        with self.transaction():
            self.conn.execute(
                """
                INSERT INTO codes (code, kind, value, max_uses, used, expires_on, referrer)
                VALUES (?, ?, ?, ?, 0, ?, ?)
                """,
                (code.upper(), kind, value, max_uses, expires_on, referrer),
            )
        return self.get(code)

    def redeem(self, code: str, user_id: str, amount: int, today: str) -> dict:
        with self.transaction():
            row = self.conn.execute("SELECT * FROM codes WHERE code = ?", (code.upper(),)).fetchone()
            if row is None:
                raise PromoError("unknown_code")
            if today > row["expires_on"]:
                raise PromoError("expired")
            if row["used"] >= row["max_uses"]:
                raise PromoError("exhausted")
            seen = self.conn.execute(
                "SELECT 1 FROM redemptions WHERE code = ? AND user_id = ?",
                (row["code"], user_id),
            ).fetchone()
            if seen is not None:
                raise PromoError("already_used")
            discount = row["value"] if row["kind"] == "fixed" else amount * row["value"] // 100
            discount = min(discount, amount)
            self.conn.execute(
                "INSERT INTO redemptions (code, user_id, discount) VALUES (?, ?, ?)",
                (row["code"], user_id, discount),
            )
            self.conn.execute("UPDATE codes SET used = used + 1 WHERE code = ?", (row["code"],))
            if row["referrer"]:
                self.conn.execute(
                    """
                    INSERT INTO credits (user_id, amount) VALUES (?, ?)
                    ON CONFLICT(user_id) DO UPDATE SET amount = amount + excluded.amount
                    """,
                    (row["referrer"], discount),
                )
        credit = 0
        if row["referrer"]:
            stored = self.conn.execute(
                "SELECT amount FROM credits WHERE user_id = ?",
                (row["referrer"],),
            ).fetchone()
            credit = stored["amount"]
        return {"code": row["code"], "discount": discount, "payable": amount - discount, "referrer_credit": credit}

    def get(self, code: str) -> dict:
        row = self.conn.execute("SELECT * FROM codes WHERE code = ?", (code.upper(),)).fetchone()
        if row is None:
            raise PromoError("unknown_code")
        return dict(row)
