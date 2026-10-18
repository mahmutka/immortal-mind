"""
agent/accounts.py

User accounts for the shared web mind.

The mind talks with many people and remembers all of them, so it has to
know who it is talking to — otherwise anyone could claim to be someone
else and ask for their private memories. Each visitor registers once with
a username + password and logs in afterwards.

Also tracks per-person and site-wide daily message counts, so the LLM bill
cannot grow without bound.

Storage: SQLite (data/accounts.db). Passwords are hashed with scrypt
(memory-hard, standard library — no extra dependency).
"""

import hashlib
import hmac
import logging
import os
import re
import sqlite3
import threading
from datetime import datetime, timedelta, timezone
from typing import Optional

logger = logging.getLogger(__name__)

USERNAME_RE = re.compile(r"^[a-z0-9_]{3,24}$")
PASSWORD_MIN_LEN = 8
PASSWORD_MAX_LEN = 128

# scrypt parameters (~16 MB memory per hash)
_SCRYPT_N = 2 ** 14
_SCRYPT_R = 8
_SCRYPT_P = 1
_SCRYPT_DKLEN = 64

# Brute-force protection
MAX_FAILED_LOGINS = 5
LOCKOUT_MINUTES = 15


class AccountError(ValueError):
    """Raised with a user-facing message when registration/login input is invalid."""


def normalize_username(username: str) -> str:
    return (username or "").strip().lower()


def _hash_password(password: str, salt: Optional[bytes] = None) -> str:
    salt = salt if salt is not None else os.urandom(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P, dklen=_SCRYPT_DKLEN,
    )
    return f"scrypt${_SCRYPT_N}${_SCRYPT_R}${_SCRYPT_P}${salt.hex()}${digest.hex()}"


def _verify_password(password: str, stored: str) -> bool:
    try:
        scheme, n, r, p, salt_hex, digest_hex = stored.split("$")
        if scheme != "scrypt":
            return False
        digest = hashlib.scrypt(
            password.encode("utf-8"),
            salt=bytes.fromhex(salt_hex), n=int(n), r=int(r), p=int(p),
            dklen=len(digest_hex) // 2,
        )
        return hmac.compare_digest(digest.hex(), digest_hex)
    except Exception:
        return False


# Verified against when the username does not exist, so a login attempt
# takes the same time whether or not the account exists.
_DUMMY_HASH = _hash_password("dummy-password-for-timing", salt=b"\x00" * 16)


class AccountStore:
    """
    SQLite-backed accounts + daily usage counters.

    Parameters:
        db_path: SQLite database file path
    """

    def __init__(self, db_path: str = "data/accounts.db") -> None:
        self.db_path = db_path
        self._lock = threading.Lock()
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS accounts (
                    username        TEXT PRIMARY KEY,
                    password_hash   TEXT NOT NULL,
                    created_at      TEXT NOT NULL,
                    last_seen       TEXT,
                    failed_logins   INTEGER DEFAULT 0,
                    locked_until    TEXT
                );
                CREATE TABLE IF NOT EXISTS usage (
                    day         TEXT NOT NULL,
                    username    TEXT NOT NULL,
                    count       INTEGER DEFAULT 0,
                    PRIMARY KEY (day, username)
                );
            """)
        try:
            os.chmod(db_path, 0o600)
        except OSError:
            pass

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.row_factory = sqlite3.Row
        return conn

    # ─────────────────────────────────────────────
    # ACCOUNTS
    # ─────────────────────────────────────────────

    def register(self, username: str, password: str) -> str:
        """
        Create an account.

        Returns:
            str: The normalized username (used as the memory owner_id)

        Raises:
            AccountError: Invalid input or username taken
        """
        username = normalize_username(username)
        if not USERNAME_RE.match(username):
            raise AccountError(
                "Username must be 3-24 characters: lowercase letters, digits or _."
            )
        if not (PASSWORD_MIN_LEN <= len(password or "") <= PASSWORD_MAX_LEN):
            raise AccountError(
                f"Password must be {PASSWORD_MIN_LEN}-{PASSWORD_MAX_LEN} characters."
            )

        password_hash = _hash_password(password)
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as conn:
            try:
                conn.execute(
                    "INSERT INTO accounts (username, password_hash, created_at) VALUES (?, ?, ?)",
                    (username, password_hash, now),
                )
            except sqlite3.IntegrityError:
                raise AccountError("This username is already taken.") from None
        logger.info("Account registered: %s", username)
        return username

    def authenticate(self, username: str, password: str) -> Optional[str]:
        """
        Check a login.

        Returns:
            str | None: The normalized username on success, None on failure

        Raises:
            AccountError: Account temporarily locked after too many failures
        """
        username = normalize_username(username)
        now = datetime.now(timezone.utc)
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT password_hash, failed_logins, locked_until FROM accounts WHERE username = ?",
                (username,),
            ).fetchone()

            if row is None:
                _verify_password(password or "", _DUMMY_HASH)
                return None

            if row["locked_until"] and datetime.fromisoformat(row["locked_until"]) > now:
                raise AccountError(
                    f"Too many failed attempts. Try again in {LOCKOUT_MINUTES} minutes."
                )

            if _verify_password(password or "", row["password_hash"]):
                conn.execute(
                    "UPDATE accounts SET failed_logins = 0, locked_until = NULL WHERE username = ?",
                    (username,),
                )
                return username

            failed = row["failed_logins"] + 1
            locked_until = None
            if failed >= MAX_FAILED_LOGINS:
                locked_until = (now + timedelta(minutes=LOCKOUT_MINUTES)).isoformat()
                failed = 0
                logger.warning("Account locked after failed logins: %s", username)
            conn.execute(
                "UPDATE accounts SET failed_logins = ?, locked_until = ? WHERE username = ?",
                (failed, locked_until, username),
            )
            return None

    def get_last_seen(self, username: str) -> Optional[datetime]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT last_seen FROM accounts WHERE username = ?", (username,)
            ).fetchone()
        if row and row["last_seen"]:
            return datetime.fromisoformat(row["last_seen"])
        return None

    def touch(self, username: str) -> None:
        """Record that this person just talked with the mind."""
        with self._lock, self._connect() as conn:
            conn.execute(
                "UPDATE accounts SET last_seen = ? WHERE username = ?",
                (datetime.now(timezone.utc).isoformat(), username),
            )

    def delete_account(self, username: str) -> None:
        with self._lock, self._connect() as conn:
            conn.execute("DELETE FROM accounts WHERE username = ?", (username,))
            conn.execute("DELETE FROM usage WHERE username = ?", (username,))
        logger.info("Account deleted: %s", username)

    def count_accounts(self) -> int:
        with self._connect() as conn:
            return conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]

    # ─────────────────────────────────────────────
    # USAGE LIMITS
    # ─────────────────────────────────────────────

    def consume_message(
        self,
        username: str,
        daily_limit: int = 0,
        global_daily_limit: int = 0,
    ) -> tuple[bool, str]:
        """
        Count one message against today's limits (UTC day).

        A limit of 0 means unlimited.

        Returns:
            tuple[bool, str]: (allowed, reason) — reason is "" when allowed,
            otherwise "user" or "global"
        """
        day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        with self._lock, self._connect() as conn:
            if global_daily_limit > 0:
                total = conn.execute(
                    "SELECT COALESCE(SUM(count), 0) FROM usage WHERE day = ?", (day,)
                ).fetchone()[0]
                if total >= global_daily_limit:
                    return False, "global"
            if daily_limit > 0:
                row = conn.execute(
                    "SELECT count FROM usage WHERE day = ? AND username = ?", (day, username)
                ).fetchone()
                if row and row["count"] >= daily_limit:
                    return False, "user"
            conn.execute(
                """INSERT INTO usage (day, username, count) VALUES (?, ?, 1)
                   ON CONFLICT(day, username) DO UPDATE SET count = count + 1""",
                (day, username),
            )
        return True, ""

    def messages_today(self, username: str) -> int:
        day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        with self._connect() as conn:
            row = conn.execute(
                "SELECT count FROM usage WHERE day = ? AND username = ?", (day, username)
            ).fetchone()
        return row["count"] if row else 0
