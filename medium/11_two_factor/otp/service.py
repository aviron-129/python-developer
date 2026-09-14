import base64
import hashlib
import hmac
import secrets
import sqlite3
import struct
import uuid
from contextlib import contextmanager


def hotp(secret: bytes, counter: int) -> str:
    digest = hmac.new(secret, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    number = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    return f"{number % 1_000_000:06d}"


def totp(secret: bytes, now: int, step: int = 30) -> str:
    return hotp(secret, now // step)


def hash_secret(value: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", value.encode(), salt, 20_000)
    return f"{salt.hex()}${digest.hex()}"


def check_secret(value: str, stored: str) -> bool:
    salt_hex, _digest = stored.split("$", 1)
    return hmac.compare_digest(hash_secret(value, bytes.fromhex(salt_hex)), stored)


class AuthError(Exception):
    def __init__(self, code: str, status: int = 401):
        self.code = code
        self.status = status
        super().__init__(code)


class TwoFactor:
    def __init__(self, path: str):
        self.now = 1_700_000_000
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                totp_secret TEXT,
                totp_enabled INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS backup_codes (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                code_hash TEXT NOT NULL,
                used INTEGER NOT NULL DEFAULT 0
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

    def register(self, email: str, password: str) -> dict:
        user_id = uuid.uuid4().hex
        with self.transaction():
            self.conn.execute(
                "INSERT INTO users (id, email, password_hash) VALUES (?, ?, ?)",
                (user_id, email.lower(), hash_secret(password)),
            )
        return {"id": user_id, "email": email.lower()}

    def enroll(self, user_id: str) -> dict:
        secret = secrets.token_bytes(20)
        encoded = base64.b32encode(secret).decode().rstrip("=")
        backups = [secrets.token_hex(4) for _ in range(3)]
        with self.transaction():
            user = self._user(user_id)
            if user is None:
                raise AuthError("unknown_user", 404)
            self.conn.execute(
                "UPDATE users SET totp_secret = ?, totp_enabled = 0 WHERE id = ?",
                (encoded, user_id),
            )
            self.conn.execute("DELETE FROM backup_codes WHERE user_id = ?", (user_id,))
            self.conn.executemany(
                "INSERT INTO backup_codes (id, user_id, code_hash) VALUES (?, ?, ?)",
                [(uuid.uuid4().hex, user_id, hash_secret(code)) for code in backups],
            )
        return {"secret": encoded, "backup_codes": backups}

    def confirm(self, user_id: str, code: str) -> dict:
        user = self._require(user_id)
        if not user["totp_secret"] or not self._matches_totp(user["totp_secret"], code):
            raise AuthError("invalid_code", 401)
        with self.transaction():
            self.conn.execute("UPDATE users SET totp_enabled = 1 WHERE id = ?", (user_id,))
        return {"enabled": True}

    def login(self, email: str, password: str, code: str) -> dict:
        user = self.conn.execute("SELECT * FROM users WHERE email = ?", (email.lower(),)).fetchone()
        if user is None or not check_secret(password, user["password_hash"]):
            raise AuthError("invalid_credentials", 401)
        if not user["totp_enabled"]:
            raise AuthError("totp_required", 401)
        if self._matches_totp(user["totp_secret"], code) or self._use_backup(user["id"], code):
            return {"user_id": user["id"], "email": user["email"]}
        raise AuthError("invalid_code", 401)

    def _matches_totp(self, encoded: str, code: str) -> bool:
        padded = encoded + "=" * ((8 - len(encoded) % 8) % 8)
        secret = base64.b32decode(padded)
        return hmac.compare_digest(totp(secret, self.now), code)

    def _use_backup(self, user_id: str, code: str) -> bool:
        rows = self.conn.execute(
            "SELECT * FROM backup_codes WHERE user_id = ? AND used = 0",
            (user_id,),
        ).fetchall()
        for row in rows:
            if check_secret(code, row["code_hash"]):
                with self.transaction():
                    self.conn.execute("UPDATE backup_codes SET used = 1 WHERE id = ?", (row["id"],))
                return True
        return False

    def _user(self, user_id: str):
        return self.conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    def _require(self, user_id: str):
        user = self._user(user_id)
        if user is None:
            raise AuthError("unknown_user", 404)
        return user
