import sqlite3
from contextlib import contextmanager

from checkout.domain import OutOfStock, UnknownSku


class Store:
    def __init__(self, path: str):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS skus (
                sku TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                on_hand INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS checkouts (
                id TEXT PRIMARY KEY,
                sku TEXT NOT NULL,
                qty INTEGER NOT NULL,
                amount INTEGER NOT NULL,
                state TEXT NOT NULL,
                payment_id TEXT,
                reason TEXT
            );
            CREATE TABLE IF NOT EXISTS steps (
                checkout_id TEXT NOT NULL,
                seq INTEGER NOT NULL,
                name TEXT NOT NULL
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

    def put_sku(self, sku: str, name: str, on_hand: int) -> None:
        self.conn.execute(
            """
            INSERT INTO skus (sku, name, on_hand) VALUES (?, ?, ?)
            ON CONFLICT(sku) DO UPDATE SET name = excluded.name, on_hand = excluded.on_hand
            """,
            (sku, name, on_hand),
        )

    def get_sku(self, sku: str):
        return self.conn.execute("SELECT * FROM skus WHERE sku = ?", (sku,)).fetchone()

    def take(self, sku: str, qty: int) -> int:
        row = self.get_sku(sku)
        if row is None:
            raise UnknownSku(sku)
        updated = self.conn.execute(
            "UPDATE skus SET on_hand = on_hand - ? WHERE sku = ? AND on_hand >= ?",
            (qty, sku, qty),
        )
        if updated.rowcount != 1:
            raise OutOfStock(sku, row["on_hand"], qty)
        return row["on_hand"] - qty

    def restore(self, sku: str, qty: int) -> None:
        self.conn.execute(
            "UPDATE skus SET on_hand = on_hand + ? WHERE sku = ?",
            (qty, sku),
        )

    def insert_checkout(self, checkout_id: str, sku: str, qty: int, amount: int) -> None:
        self.conn.execute(
            """
            INSERT INTO checkouts (id, sku, qty, amount, state)
            VALUES (?, ?, ?, ?, 'started')
            """,
            (checkout_id, sku, qty, amount),
        )

    def mark(self, checkout_id: str, state: str, payment_id: str | None = None, reason: str | None = None) -> None:
        self.conn.execute(
            """
            UPDATE checkouts
            SET state = ?, payment_id = COALESCE(?, payment_id), reason = COALESCE(?, reason)
            WHERE id = ?
            """,
            (state, payment_id, reason, checkout_id),
        )

    def add_step(self, checkout_id: str, name: str) -> None:
        seq = self.conn.execute(
            "SELECT COALESCE(MAX(seq), 0) + 1 FROM steps WHERE checkout_id = ?",
            (checkout_id,),
        ).fetchone()[0]
        self.conn.execute(
            "INSERT INTO steps (checkout_id, seq, name) VALUES (?, ?, ?)",
            (checkout_id, seq, name),
        )

    def read_checkout(self, checkout_id: str):
        row = self.conn.execute("SELECT * FROM checkouts WHERE id = ?", (checkout_id,)).fetchone()
        if row is None:
            return None
        steps = self.conn.execute(
            "SELECT name FROM steps WHERE checkout_id = ? ORDER BY seq",
            (checkout_id,),
        ).fetchall()
        payload = dict(row)
        payload["steps"] = [step["name"] for step in steps]
        return payload
