import hashlib
import sqlite3
from contextlib import contextmanager


class Flags:
    def __init__(self, path: str):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS flags (
                name TEXT PRIMARY KEY,
                percent INTEGER NOT NULL,
                allow_tenants TEXT NOT NULL
            )
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

    def put(self, name: str, percent: int, allow_tenants: list[str]) -> dict:
        with self.transaction():
            self.conn.execute(
                """
                INSERT INTO flags (name, percent, allow_tenants) VALUES (?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET percent = excluded.percent, allow_tenants = excluded.allow_tenants
                """,
                (name, percent, ",".join(allow_tenants)),
            )
        return self.get(name)

    def evaluate(self, name: str, user_id: str, tenant: str) -> dict:
        row = self.conn.execute("SELECT * FROM flags WHERE name = ?", (name,)).fetchone()
        if row is None:
            return {"name": name, "enabled": False, "reason": "missing"}
        allowed = [item for item in row["allow_tenants"].split(",") if item]
        if tenant in allowed:
            return {"name": name, "enabled": True, "reason": "allowlist"}
        bucket = int(hashlib.sha256(f"{name}:{user_id}".encode()).hexdigest(), 16) % 100
        enabled = bucket < row["percent"]
        return {"name": name, "enabled": enabled, "reason": "percent", "bucket": bucket}

    def get(self, name: str) -> dict:
        row = self.conn.execute("SELECT * FROM flags WHERE name = ?", (name,)).fetchone()
        return {
            "name": row["name"],
            "percent": row["percent"],
            "allow_tenants": [item for item in row["allow_tenants"].split(",") if item],
        }
