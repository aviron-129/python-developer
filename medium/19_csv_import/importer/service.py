import sqlite3
from contextlib import contextmanager


class Importer:
    def __init__(self, path: str):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS products (sku TEXT PRIMARY KEY, name TEXT NOT NULL, qty INTEGER NOT NULL)"
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

    def load(self, text: str) -> dict:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        accepted = []
        errors = []
        seen: set[str] = set()
        with self.transaction():
            for index, line in enumerate(lines, start=1):
                parts = [part.strip() for part in line.split(",")]
                if len(parts) != 3:
                    errors.append({"line": index, "reason": "bad_columns"})
                    continue
                sku, name, raw_qty = parts
                if not sku or not name or not raw_qty.isdigit():
                    errors.append({"line": index, "reason": "invalid_row", "sku": sku})
                    continue
                if sku in seen or self.conn.execute("SELECT 1 FROM products WHERE sku = ?", (sku,)).fetchone():
                    errors.append({"line": index, "reason": "duplicate", "sku": sku})
                    continue
                qty = int(raw_qty)
                self.conn.execute(
                    "INSERT INTO products (sku, name, qty) VALUES (?, ?, ?)",
                    (sku, name, qty),
                )
                seen.add(sku)
                accepted.append({"sku": sku, "name": name, "qty": qty})
        return {"accepted": accepted, "errors": errors}

    def products(self) -> list[dict]:
        return [dict(row) for row in self.conn.execute("SELECT * FROM products ORDER BY sku")]
