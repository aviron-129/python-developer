import json
import sqlite3
from contextlib import contextmanager


class Incompatible(Exception):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


class InvalidPayload(Exception):
    def __init__(self, missing: list[str]):
        self.missing = missing
        super().__init__(",".join(missing))


class Registry:
    def __init__(self, path: str):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schemas (
                name TEXT NOT NULL,
                version INTEGER NOT NULL,
                required TEXT NOT NULL,
                optional TEXT NOT NULL,
                PRIMARY KEY (name, version)
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

    def register(self, name: str, required: list[str], optional: list[str]) -> dict:
        previous = self.conn.execute(
            "SELECT * FROM schemas WHERE name = ? ORDER BY version DESC LIMIT 1",
            (name,),
        ).fetchone()
        if previous is not None:
            old_required = set(json.loads(previous["required"]))
            if not old_required <= set(required):
                raise Incompatible("required_removed")
            old_optional = set(json.loads(previous["optional"]))
            if (old_required | old_optional) - set(required) - set(optional):
                raise Incompatible("field_removed")
        version = 1 if previous is None else previous["version"] + 1
        with self.transaction():
            self.conn.execute(
                "INSERT INTO schemas (name, version, required, optional) VALUES (?, ?, ?, ?)",
                (name, version, json.dumps(required), json.dumps(optional)),
            )
        return self.get(name, version)

    def validate(self, name: str, version: int, payload: dict) -> dict:
        row = self._row(name, version)
        missing = [field for field in json.loads(row["required"]) if field not in payload]
        if missing:
            raise InvalidPayload(missing)
        return {"name": name, "version": version, "ok": True}

    def get(self, name: str, version: int) -> dict:
        row = self._row(name, version)
        return {
            "name": row["name"],
            "version": row["version"],
            "required": json.loads(row["required"]),
            "optional": json.loads(row["optional"]),
        }

    def _row(self, name: str, version: int):
        row = self.conn.execute(
            "SELECT * FROM schemas WHERE name = ? AND version = ?",
            (name, version),
        ).fetchone()
        if row is None:
            raise Incompatible("unknown_schema")
        return row
