import sqlite3
import uuid
from contextlib import contextmanager

from inventory.domain import (
    IllegalTransition,
    InsufficientStock,
    UnknownReservation,
    UnknownSku,
    VersionConflict,
)


class Ledger:
    def __init__(self, path: str):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS items (
                sku TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                on_hand INTEGER NOT NULL,
                reserved INTEGER NOT NULL,
                version INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS reservations (
                id TEXT PRIMARY KEY,
                sku TEXT NOT NULL,
                qty INTEGER NOT NULL,
                order_ref TEXT NOT NULL,
                status TEXT NOT NULL
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

    def add_item(self, sku: str, name: str, on_hand: int) -> dict:
        with self.transaction():
            self.conn.execute(
                """
                INSERT INTO items (sku, name, on_hand, reserved, version)
                VALUES (?, ?, ?, 0, 1)
                """,
                (sku, name, on_hand),
            )
        return self.item(sku)

    def item(self, sku: str) -> dict:
        row = self.conn.execute("SELECT * FROM items WHERE sku = ?", (sku,)).fetchone()
        if row is None:
            raise UnknownSku(sku)
        payload = dict(row)
        payload["available"] = payload["on_hand"] - payload["reserved"]
        return payload

    def receive(self, sku: str, qty: int, expected_version: int) -> dict:
        with self.transaction():
            current = self._row(sku)
            if current["version"] != expected_version:
                raise VersionConflict(sku)
            self.conn.execute(
                """
                UPDATE items
                SET on_hand = on_hand + ?, version = version + 1
                WHERE sku = ? AND version = ?
                """,
                (qty, sku, expected_version),
            )
        return self.item(sku)

    def reserve(self, sku: str, qty: int, order_ref: str) -> dict:
        reservation_id = uuid.uuid4().hex
        with self.transaction():
            current = self._row(sku)
            available = current["on_hand"] - current["reserved"]
            if available < qty:
                raise InsufficientStock(sku, available, qty)
            updated = self.conn.execute(
                """
                UPDATE items
                SET reserved = reserved + ?, version = version + 1
                WHERE sku = ? AND version = ? AND (on_hand - reserved) >= ?
                """,
                (qty, sku, current["version"], qty),
            )
            if updated.rowcount != 1:
                raise VersionConflict(sku)
            self.conn.execute(
                """
                INSERT INTO reservations (id, sku, qty, order_ref, status)
                VALUES (?, ?, ?, ?, 'held')
                """,
                (reservation_id, sku, qty, order_ref),
            )
        return self.reservation(reservation_id)

    def commit(self, reservation_id: str) -> dict:
        return self._finish(reservation_id, "committed", sell=True)

    def release(self, reservation_id: str) -> dict:
        return self._finish(reservation_id, "released", sell=False)

    def reservation(self, reservation_id: str) -> dict:
        row = self.conn.execute(
            "SELECT * FROM reservations WHERE id = ?",
            (reservation_id,),
        ).fetchone()
        if row is None:
            raise UnknownReservation(reservation_id)
        return dict(row)

    def _finish(self, reservation_id: str, status: str, sell: bool) -> dict:
        with self.transaction():
            row = self.conn.execute(
                "SELECT * FROM reservations WHERE id = ?",
                (reservation_id,),
            ).fetchone()
            if row is None:
                raise UnknownReservation(reservation_id)
            if row["status"] != "held":
                raise IllegalTransition(row["status"])
            if sell:
                self.conn.execute(
                    """
                    UPDATE items
                    SET on_hand = on_hand - ?, reserved = reserved - ?, version = version + 1
                    WHERE sku = ?
                    """,
                    (row["qty"], row["qty"], row["sku"]),
                )
            else:
                self.conn.execute(
                    """
                    UPDATE items
                    SET reserved = reserved - ?, version = version + 1
                    WHERE sku = ?
                    """,
                    (row["qty"], row["sku"]),
                )
            self.conn.execute(
                "UPDATE reservations SET status = ? WHERE id = ?",
                (status, reservation_id),
            )
        return self.reservation(reservation_id)

    def _row(self, sku: str):
        row = self.conn.execute("SELECT * FROM items WHERE sku = ?", (sku,)).fetchone()
        if row is None:
            raise UnknownSku(sku)
        return row
