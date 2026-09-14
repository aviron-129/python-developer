import json
import sqlite3
import uuid
from contextlib import contextmanager


class UnknownOrder(Exception):
    pass


class Source:
    def __init__(self, path: str):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id TEXT PRIMARY KEY,
                sku TEXT NOT NULL,
                total INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS changelog (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                op TEXT NOT NULL,
                order_id TEXT NOT NULL,
                payload TEXT,
                projected INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS order_view (
                id TEXT PRIMARY KEY,
                sku TEXT NOT NULL,
                total INTEGER NOT NULL
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

    def create(self, sku: str, total: int) -> dict:
        order_id = uuid.uuid4().hex
        payload = {"sku": sku, "total": total}
        with self.transaction():
            self.conn.execute("INSERT INTO orders (id, sku, total) VALUES (?, ?, ?)", (order_id, sku, total))
            self._change("insert", order_id, payload)
        return {"id": order_id, **payload}

    def update(self, order_id: str, total: int) -> dict:
        row = self._order(order_id)
        payload = {"sku": row["sku"], "total": total}
        with self.transaction():
            self.conn.execute("UPDATE orders SET total = ? WHERE id = ?", (total, order_id))
            self._change("update", order_id, payload)
        return {"id": order_id, **payload}

    def delete(self, order_id: str) -> dict:
        self._order(order_id)
        with self.transaction():
            self.conn.execute("DELETE FROM orders WHERE id = ?", (order_id,))
            self._change("delete", order_id, None)
        return {"id": order_id, "deleted": True}

    def project(self) -> dict:
        rows = self.conn.execute("SELECT * FROM changelog WHERE projected = 0 ORDER BY id").fetchall()
        with self.transaction():
            for row in rows:
                payload = json.loads(row["payload"]) if row["payload"] else None
                if row["op"] == "delete":
                    self.conn.execute("DELETE FROM order_view WHERE id = ?", (row["order_id"],))
                else:
                    self.conn.execute(
                        """
                        INSERT INTO order_view (id, sku, total) VALUES (?, ?, ?)
                        ON CONFLICT(id) DO UPDATE SET sku = excluded.sku, total = excluded.total
                        """,
                        (row["order_id"], payload["sku"], payload["total"]),
                    )
                self.conn.execute("UPDATE changelog SET projected = 1 WHERE id = ?", (row["id"],))
        return {"applied": len(rows)}

    def view(self) -> list[dict]:
        return [dict(row) for row in self.conn.execute("SELECT * FROM order_view ORDER BY id")]

    def _change(self, op: str, order_id: str, payload: dict | None) -> None:
        self.conn.execute(
            "INSERT INTO changelog (op, order_id, payload) VALUES (?, ?, ?)",
            (op, order_id, None if payload is None else json.dumps(payload)),
        )

    def _order(self, order_id: str):
        row = self.conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        if row is None:
            raise UnknownOrder()
        return row
