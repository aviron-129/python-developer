import sqlite3
from contextlib import contextmanager


class UnknownInvoice(Exception):
    pass


class Invoices:
    def __init__(self, path: str):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS counter (id INTEGER PRIMARY KEY CHECK (id = 1), value INTEGER NOT NULL);
            INSERT OR IGNORE INTO counter (id, value) VALUES (1, 0);
            CREATE TABLE IF NOT EXISTS invoices (
                number TEXT PRIMARY KEY,
                customer TEXT NOT NULL,
                total INTEGER NOT NULL,
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

    def issue(self, customer: str, total: int) -> dict:
        with self.transaction():
            current = self.conn.execute("SELECT value FROM counter WHERE id = 1").fetchone()["value"]
            nxt = current + 1
            number = f"INV-{nxt:04d}"
            self.conn.execute("UPDATE counter SET value = ? WHERE id = 1", (nxt,))
            self.conn.execute(
                "INSERT INTO invoices (number, customer, total, status) VALUES (?, ?, ?, 'issued')",
                (number, customer, total),
            )
        return self.get(number)

    def void(self, number: str) -> dict:
        self.get(number)
        with self.transaction():
            self.conn.execute("UPDATE invoices SET status = 'void' WHERE number = ?", (number,))
        return self.get(number)

    def get(self, number: str) -> dict:
        row = self.conn.execute("SELECT * FROM invoices WHERE number = ?", (number,)).fetchone()
        if row is None:
            raise UnknownInvoice()
        return dict(row)
