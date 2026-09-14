import sqlite3
import uuid
from contextlib import contextmanager


class Overlap(Exception):
    pass


class UnknownBooking(Exception):
    pass


def overlaps(start: str, end: str, other_start: str, other_end: str) -> bool:
    return start < other_end and end > other_start


class Calendar:
    def __init__(self, path: str):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS resources (code TEXT PRIMARY KEY, name TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS bookings (
                id TEXT PRIMARY KEY,
                resource TEXT NOT NULL,
                start_at TEXT NOT NULL,
                end_at TEXT NOT NULL,
                guest TEXT NOT NULL,
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

    def add_resource(self, code: str, name: str) -> dict:
        with self.transaction():
            self.conn.execute("INSERT INTO resources (code, name) VALUES (?, ?)", (code, name))
        return {"code": code, "name": name}

    def book(self, resource: str, start_at: str, end_at: str, guest: str) -> dict:
        if end_at <= start_at:
            raise Overlap()
        booking_id = uuid.uuid4().hex
        with self.transaction():
            rows = self.conn.execute(
                "SELECT start_at, end_at FROM bookings WHERE resource = ? AND status = 'booked'",
                (resource,),
            )
            for row in rows:
                if overlaps(start_at, end_at, row["start_at"], row["end_at"]):
                    raise Overlap()
            self.conn.execute(
                """
                INSERT INTO bookings (id, resource, start_at, end_at, guest, status)
                VALUES (?, ?, ?, ?, ?, 'booked')
                """,
                (booking_id, resource, start_at, end_at, guest),
            )
        return self.get(booking_id)

    def cancel(self, booking_id: str) -> dict:
        self.get(booking_id)
        with self.transaction():
            self.conn.execute("UPDATE bookings SET status = 'canceled' WHERE id = ?", (booking_id,))
        return self.get(booking_id)

    def get(self, booking_id: str) -> dict:
        row = self.conn.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,)).fetchone()
        if row is None:
            raise UnknownBooking()
        return dict(row)
