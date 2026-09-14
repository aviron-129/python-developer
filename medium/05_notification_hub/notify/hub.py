import json
import sqlite3
import uuid
from contextlib import contextmanager

from notify.domain import CHANNELS, MissingPlaceholder, UnknownRecipient, UnknownTemplate


def render(template: str, payload: dict) -> str:
    try:
        return template.format(**payload)
    except KeyError as exc:
        raise MissingPlaceholder(str(exc).strip("'")) from exc


class RecordingBus:
    def __init__(self):
        self.sent: list[dict] = []

    def send(self, channel: str, address: str, body: str) -> str:
        message_id = uuid.uuid4().hex
        self.sent.append(
            {"id": message_id, "channel": channel, "address": address, "body": body}
        )
        return message_id


class Hub:
    def __init__(self, path: str, bus: RecordingBus):
        self.bus = bus
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS recipients (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                push_token TEXT NOT NULL,
                telegram_chat TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS preferences (
                recipient_id TEXT NOT NULL,
                channel TEXT NOT NULL,
                enabled INTEGER NOT NULL,
                PRIMARY KEY (recipient_id, channel)
            );
            CREATE TABLE IF NOT EXISTS templates (
                code TEXT PRIMARY KEY,
                body TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS notifications (
                id TEXT PRIMARY KEY,
                recipient_id TEXT NOT NULL,
                template_code TEXT NOT NULL,
                payload TEXT NOT NULL,
                status TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS deliveries (
                id TEXT PRIMARY KEY,
                notification_id TEXT NOT NULL,
                channel TEXT NOT NULL,
                status TEXT NOT NULL,
                detail TEXT NOT NULL
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

    def add_recipient(self, name: str, email: str, push_token: str, telegram_chat: str) -> dict:
        recipient_id = uuid.uuid4().hex
        with self.transaction():
            self.conn.execute(
                """
                INSERT INTO recipients (id, name, email, push_token, telegram_chat)
                VALUES (?, ?, ?, ?, ?)
                """,
                (recipient_id, name, email, push_token, telegram_chat),
            )
            self.conn.executemany(
                "INSERT INTO preferences (recipient_id, channel, enabled) VALUES (?, ?, 1)",
                [(recipient_id, channel) for channel in CHANNELS],
            )
        return self.recipient(recipient_id)

    def set_preferences(self, recipient_id: str, enabled: dict) -> dict:
        self.recipient(recipient_id)
        unknown = set(enabled) - set(CHANNELS)
        if unknown:
            raise ValueError(",".join(sorted(unknown)))
        with self.transaction():
            for channel, flag in enabled.items():
                self.conn.execute(
                    """
                    UPDATE preferences SET enabled = ?
                    WHERE recipient_id = ? AND channel = ?
                    """,
                    (1 if flag else 0, recipient_id, channel),
                )
        return self.recipient(recipient_id)

    def put_template(self, code: str, body: str) -> dict:
        with self.transaction():
            self.conn.execute(
                """
                INSERT INTO templates (code, body) VALUES (?, ?)
                ON CONFLICT(code) DO UPDATE SET body = excluded.body
                """,
                (code, body),
            )
        return {"code": code, "body": body}

    def dispatch(self, recipient_id: str, template_code: str, payload: dict) -> dict:
        person = self.recipient(recipient_id)
        template = self.conn.execute(
            "SELECT body FROM templates WHERE code = ?",
            (template_code,),
        ).fetchone()
        if template is None:
            raise UnknownTemplate(template_code)
        body = render(template["body"], payload)
        notification_id = uuid.uuid4().hex
        addresses = {
            "email": person["email"],
            "push": person["push_token"],
            "telegram": person["telegram_chat"],
        }
        sent_any = False
        deliveries = []
        with self.transaction():
            for channel in CHANNELS:
                enabled = self.conn.execute(
                    """
                    SELECT enabled FROM preferences
                    WHERE recipient_id = ? AND channel = ?
                    """,
                    (recipient_id, channel),
                ).fetchone()["enabled"]
                if not enabled:
                    deliveries.append(self._delivery(notification_id, channel, "skipped", "muted"))
                    continue
                message_id = self.bus.send(channel, addresses[channel], body)
                deliveries.append(self._delivery(notification_id, channel, "sent", message_id))
                sent_any = True
            status = "dispatched" if sent_any else "suppressed"
            self.conn.execute(
                """
                INSERT INTO notifications (id, recipient_id, template_code, payload, status)
                VALUES (?, ?, ?, ?, ?)
                """,
                (notification_id, recipient_id, template_code, json.dumps(payload, ensure_ascii=False), status),
            )
            self.conn.executemany(
                """
                INSERT INTO deliveries (id, notification_id, channel, status, detail)
                VALUES (?, ?, ?, ?, ?)
                """,
                deliveries,
            )
        return self.notification(notification_id)

    def recipient(self, recipient_id: str) -> dict:
        row = self.conn.execute(
            "SELECT * FROM recipients WHERE id = ?",
            (recipient_id,),
        ).fetchone()
        if row is None:
            raise UnknownRecipient(recipient_id)
        prefs = self.conn.execute(
            "SELECT channel, enabled FROM preferences WHERE recipient_id = ?",
            (recipient_id,),
        ).fetchall()
        payload = dict(row)
        payload["preferences"] = {item["channel"]: bool(item["enabled"]) for item in prefs}
        return payload

    def notification(self, notification_id: str) -> dict:
        row = self.conn.execute(
            "SELECT * FROM notifications WHERE id = ?",
            (notification_id,),
        ).fetchone()
        deliveries = self.conn.execute(
            "SELECT channel, status, detail FROM deliveries WHERE notification_id = ? ORDER BY channel",
            (notification_id,),
        ).fetchall()
        payload = dict(row)
        payload["payload"] = json.loads(payload["payload"])
        payload["deliveries"] = [dict(item) for item in deliveries]
        return payload

    def _delivery(self, notification_id: str, channel: str, status: str, detail: str) -> tuple:
        return (uuid.uuid4().hex, notification_id, channel, status, detail)
