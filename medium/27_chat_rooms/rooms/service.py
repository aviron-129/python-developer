import sqlite3
import uuid
from contextlib import contextmanager


class NotMember(Exception):
    pass


class UnknownRoom(Exception):
    pass


class Rooms:
    def __init__(self, path: str):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS rooms (id TEXT PRIMARY KEY, title TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS members (room_id TEXT NOT NULL, user_id TEXT NOT NULL, online INTEGER NOT NULL, PRIMARY KEY (room_id, user_id));
            CREATE TABLE IF NOT EXISTS messages (id TEXT PRIMARY KEY, room_id TEXT NOT NULL, user_id TEXT NOT NULL, body TEXT NOT NULL, seq INTEGER NOT NULL);
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

    def create(self, title: str, owner: str) -> dict:
        room_id = uuid.uuid4().hex
        with self.transaction():
            self.conn.execute("INSERT INTO rooms (id, title) VALUES (?, ?)", (room_id, title))
            self.conn.execute(
                "INSERT INTO members (room_id, user_id, online) VALUES (?, ?, 1)",
                (room_id, owner),
            )
        return {"id": room_id, "title": title}

    def join(self, room_id: str, user_id: str) -> dict:
        self._room(room_id)
        with self.transaction():
            self.conn.execute(
                """
                INSERT INTO members (room_id, user_id, online) VALUES (?, ?, 1)
                ON CONFLICT(room_id, user_id) DO UPDATE SET online = 1
                """,
                (room_id, user_id),
            )
        return {"room_id": room_id, "user_id": user_id, "online": True}

    def presence(self, room_id: str, user_id: str, online: bool) -> dict:
        self._member(room_id, user_id)
        with self.transaction():
            self.conn.execute(
                "UPDATE members SET online = ? WHERE room_id = ? AND user_id = ?",
                (1 if online else 0, room_id, user_id),
            )
        return {"room_id": room_id, "user_id": user_id, "online": online}

    def post(self, room_id: str, user_id: str, body: str) -> dict:
        self._member(room_id, user_id)
        message_id = uuid.uuid4().hex
        with self.transaction():
            seq = self.conn.execute(
                "SELECT COALESCE(MAX(seq), 0) + 1 FROM messages WHERE room_id = ?",
                (room_id,),
            ).fetchone()[0]
            self.conn.execute(
                "INSERT INTO messages (id, room_id, user_id, body, seq) VALUES (?, ?, ?, ?, ?)",
                (message_id, room_id, user_id, body, seq),
            )
        return {"id": message_id, "room_id": room_id, "user_id": user_id, "body": body, "seq": seq}

    def history(self, room_id: str) -> list[dict]:
        self._room(room_id)
        rows = self.conn.execute(
            "SELECT id, user_id, body, seq FROM messages WHERE room_id = ? ORDER BY seq",
            (room_id,),
        )
        return [dict(row) for row in rows]

    def online(self, room_id: str) -> list[str]:
        rows = self.conn.execute(
            "SELECT user_id FROM members WHERE room_id = ? AND online = 1 ORDER BY user_id",
            (room_id,),
        )
        return [row["user_id"] for row in rows]

    def _room(self, room_id: str) -> None:
        if self.conn.execute("SELECT 1 FROM rooms WHERE id = ?", (room_id,)).fetchone() is None:
            raise UnknownRoom()

    def _member(self, room_id: str, user_id: str) -> None:
        self._room(room_id)
        row = self.conn.execute(
            "SELECT 1 FROM members WHERE room_id = ? AND user_id = ?",
            (room_id, user_id),
        ).fetchone()
        if row is None:
            raise NotMember()
