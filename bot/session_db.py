import os
import sqlite3
from datetime import datetime, timezone
from typing import Any


DEFAULT_DB_PATH = os.getenv(
    "SESSION_DB_PATH",
    os.path.join(os.path.dirname(__file__), "sessions.db"),
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _connect(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = DEFAULT_DB_PATH) -> None:
    """
    セッションDBを初期化．テーブルが存在しない場合は作成する．
    """
    with _connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS thread_sessions (
                thread_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                first_prompt TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def get_thread_session(thread_id: str, db_path: str = DEFAULT_DB_PATH) -> dict[str, Any] | None:
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT thread_id, session_id, first_prompt, status, created_at, updated_at "
            "FROM thread_sessions WHERE thread_id = ?",
            (thread_id,),
        ).fetchone()
    return dict(row) if row else None


def create_thread_session(
    thread_id: str,
    session_id: str,
    first_prompt: str,
    db_path: str = DEFAULT_DB_PATH,
) -> None:
    """
    新規セッションの構築
    """
    now = _utc_now()
    with _connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO thread_sessions(thread_id, session_id, first_prompt, status, created_at, updated_at)
            VALUES(?, ?, ?, 'active', ?, ?)
            """,
            (thread_id, session_id, first_prompt, now, now),
        )
        conn.commit()


def touch_thread_session(
    thread_id: str,
    status: str = "active",
    db_path: str = DEFAULT_DB_PATH,
) -> None:
    """
    入力された thread_id のセッションの updated_at を現在時刻に更新し、必要に応じて status も更新する。
    """
    now = _utc_now()
    with _connect(db_path) as conn:
        conn.execute(
            "UPDATE thread_sessions SET status = ?, updated_at = ? WHERE thread_id = ?",
            (status, now, thread_id),
        )
        conn.commit()