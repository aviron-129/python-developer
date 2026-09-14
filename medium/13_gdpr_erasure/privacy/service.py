import json
import sqlite3
import uuid
from contextlib import contextmanager


class UnknownUser(Exception):
    pass


class Privacy:
    def __init__(self, path: str):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS people (
                id TEXT PRIMARY KEY,
                name TEXT,
                email TEXT,
                erased INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS orders (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                total INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS exports (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                body TEXT NOT NULL
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

    def add_user(self, name: str, email: str) -> dict:
        user_id = uuid.uuid4().hex
        with self.transaction():
            self.conn.execute(
                "INSERT INTO people (id, name, email) VALUES (?, ?, ?)",
                (user_id, name, email),
            )
        return self.user(user_id)

    def add_order(self, user_id: str, title: str, total: int) -> dict:
        self.user(user_id)
        order_id = uuid.uuid4().hex
        with self.transaction():
            self.conn.execute(
                "INSERT INTO orders (id, user_id, title, total) VALUES (?, ?, ?, ?)",
                (order_id, user_id, title, total),
            )
        return {"id": order_id, "user_id": user_id, "title": title, "total": total}

    def export(self, user_id: str) -> dict:
        person = self.user(user_id)
        orders = [
            dict(row)
            for row in self.conn.execute("SELECT id, title, total FROM orders WHERE user_id = ?", (user_id,))
        ]
        body = {
            "user": {"id": person["id"], "name": person["name"], "email": person["email"], "erased": bool(person["erased"])},
            "orders": orders,
        }
        export_id = uuid.uuid4().hex
        with self.transaction():
            self.conn.execute(
                "INSERT INTO exports (id, user_id, body) VALUES (?, ?, ?)",
                (export_id, user_id, json.dumps(body, ensure_ascii=False)),
            )
        return {"id": export_id, **body}

    def erase(self, user_id: str) -> dict:
        self.user(user_id)
        with self.transaction():
            self.conn.execute(
                "UPDATE people SET name = NULL, email = NULL, erased = 1 WHERE id = ?",
                (user_id,),
            )
        return self.user(user_id)

    def user(self, user_id: str) -> dict:
        row = self.conn.execute("SELECT * FROM people WHERE id = ?", (user_id,)).fetchone()
        if row is None:
            raise UnknownUser()
        payload = dict(row)
        payload["erased"] = bool(payload["erased"])
        return payload
