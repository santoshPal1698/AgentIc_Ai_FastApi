"""
SQLite persistence layer. No credentials (SMTP passwords) are ever written
here — only API keys (hashed), templates, and campaign progress/status.
"""

import sqlite3
import hashlib
import secrets
import threading
from contextlib import contextmanager
from datetime import datetime, timezone

from app.config import DB_PATH

_local = threading.local()


def get_conn():
    if not hasattr(_local, "conn"):
        _local.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _local.conn.row_factory = sqlite3.Row
    return _local.conn


@contextmanager
def db_cursor():
    conn = get_conn()
    cur = conn.cursor()
    try:
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()


def init_db():
    with db_cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                api_key_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS templates (
                user_id TEXT PRIMARY KEY,
                subject TEXT NOT NULL,
                body TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS campaigns (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                sent INTEGER DEFAULT 0,
                failed INTEGER DEFAULT 0,
                total INTEGER DEFAULT 0,
                last_error TEXT,
                created_at TEXT NOT NULL,
                finished_at TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)


def _hash_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()


def create_user(email: str) -> tuple[str, str]:
    """Returns (user_id, plaintext_api_key). The plaintext key is shown ONCE
    and never stored — only its hash is kept, like a password."""
    user_id = secrets.token_hex(8)
    api_key = secrets.token_urlsafe(32)
    with db_cursor() as cur:
        cur.execute(
            "INSERT INTO users (id, email, api_key_hash, created_at) VALUES (?, ?, ?, ?)",
            (user_id, email, _hash_key(api_key), datetime.now(timezone.utc).isoformat()),
        )
    return user_id, api_key


def get_user_by_api_key(api_key: str):
    key_hash = _hash_key(api_key)
    with db_cursor() as cur:
        cur.execute("SELECT * FROM users WHERE api_key_hash = ?", (key_hash,))
        return cur.fetchone()


def upsert_template(user_id: str, subject: str, body: str):
    with db_cursor() as cur:
        cur.execute("""
            INSERT INTO templates (user_id, subject, body, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET subject=excluded.subject,
                body=excluded.body, updated_at=excluded.updated_at
        """, (user_id, subject, body, datetime.now(timezone.utc).isoformat()))


def get_template(user_id: str):
    with db_cursor() as cur:
        cur.execute("SELECT * FROM templates WHERE user_id = ?", (user_id,))
        return cur.fetchone()


def create_campaign(campaign_id: str, user_id: str, total: int):
    with db_cursor() as cur:
        cur.execute("""
            INSERT INTO campaigns (id, user_id, status, total, created_at)
            VALUES (?, ?, 'running', ?, ?)
        """, (campaign_id, user_id, total, datetime.now(timezone.utc).isoformat()))


def update_campaign_progress(campaign_id: str, sent: int = None, failed: int = None,
                              status: str = None, last_error: str = None, finished: bool = False):
    fields, values = [], []
    if sent is not None:
        fields.append("sent = ?"); values.append(sent)
    if failed is not None:
        fields.append("failed = ?"); values.append(failed)
    if status is not None:
        fields.append("status = ?"); values.append(status)
    if last_error is not None:
        fields.append("last_error = ?"); values.append(last_error)
    if finished:
        fields.append("finished_at = ?"); values.append(datetime.now(timezone.utc).isoformat())
    if not fields:
        return
    values.append(campaign_id)
    with db_cursor() as cur:
        cur.execute(f"UPDATE campaigns SET {', '.join(fields)} WHERE id = ?", values)


def get_campaign(campaign_id: str, user_id: str):
    with db_cursor() as cur:
        cur.execute("SELECT * FROM campaigns WHERE id = ? AND user_id = ?", (campaign_id, user_id))
        return cur.fetchone()


def list_campaigns(user_id: str):
    with db_cursor() as cur:
        cur.execute("SELECT * FROM campaigns WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        return cur.fetchall()
