import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone


class UnknownPlan(Exception):
    pass


class UnknownSubscription(Exception):
    pass


class Clock:
    def __init__(self):
        self.now = datetime(2026, 9, 1, tzinfo=timezone.utc)

    def advance(self, days: int) -> None:
        self.now += timedelta(days=days)


class Subscriptions:
    def __init__(self, path: str, clock: Clock | None = None):
        self.clock = clock or Clock()
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS plans (
                code TEXT PRIMARY KEY,
                price INTEGER NOT NULL,
                trial_days INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS subscriptions (
                id TEXT PRIMARY KEY,
                plan_code TEXT NOT NULL,
                card_token TEXT NOT NULL,
                status TEXT NOT NULL,
                renews_at TEXT NOT NULL,
                failures INTEGER NOT NULL DEFAULT 0
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

    def add_plan(self, code: str, price: int, trial_days: int) -> dict:
        with self.transaction():
            self.conn.execute(
                "INSERT INTO plans (code, price, trial_days) VALUES (?, ?, ?)",
                (code, price, trial_days),
            )
        return dict(self.conn.execute("SELECT * FROM plans WHERE code = ?", (code,)).fetchone())

    def subscribe(self, plan_code: str, card_token: str) -> dict:
        plan = self.conn.execute("SELECT * FROM plans WHERE code = ?", (plan_code,)).fetchone()
        if plan is None:
            raise UnknownPlan()
        sub_id = uuid.uuid4().hex
        renews = (self.clock.now + timedelta(days=plan["trial_days"] or 30)).isoformat()
        status = "trialing" if plan["trial_days"] else "active"
        with self.transaction():
            self.conn.execute(
                """
                INSERT INTO subscriptions (id, plan_code, card_token, status, renews_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (sub_id, plan_code, card_token, status, renews),
            )
        return self.get(sub_id)

    def run_billing(self) -> list[dict]:
        due = self.conn.execute(
            "SELECT * FROM subscriptions WHERE status IN ('trialing', 'active', 'past_due') AND renews_at <= ?",
            (self.clock.now.isoformat(),),
        ).fetchall()
        changed = []
        for row in due:
            changed.append(self._charge(row["id"]))
        return changed

    def cancel(self, sub_id: str) -> dict:
        self.get(sub_id)
        with self.transaction():
            self.conn.execute("UPDATE subscriptions SET status = 'canceled' WHERE id = ?", (sub_id,))
        return self.get(sub_id)

    def get(self, sub_id: str) -> dict:
        row = self.conn.execute("SELECT * FROM subscriptions WHERE id = ?", (sub_id,)).fetchone()
        if row is None:
            raise UnknownSubscription()
        return dict(row)

    def _charge(self, sub_id: str) -> dict:
        row = self.conn.execute("SELECT * FROM subscriptions WHERE id = ?", (sub_id,)).fetchone()
        plan = self.conn.execute("SELECT * FROM plans WHERE code = ?", (row["plan_code"],)).fetchone()
        declined = row["card_token"] == "decline" or plan["price"] <= 0
        with self.transaction():
            if declined:
                failures = row["failures"] + 1
                status = "canceled" if failures >= 2 else "past_due"
                self.conn.execute(
                    "UPDATE subscriptions SET status = ?, failures = ? WHERE id = ?",
                    (status, failures, sub_id),
                )
            else:
                renews = (self.clock.now + timedelta(days=30)).isoformat()
                self.conn.execute(
                    """
                    UPDATE subscriptions
                    SET status = 'active', failures = 0, renews_at = ?
                    WHERE id = ?
                    """,
                    (renews, sub_id),
                )
        return self.get(sub_id)
