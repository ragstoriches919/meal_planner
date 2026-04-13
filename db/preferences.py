from __future__ import annotations

from db.connection import get_connection


def get_preferences() -> dict:
    """Return the single user preferences row."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT vegetarian FROM user_preferences LIMIT 1")
            return cur.fetchone()


def set_vegetarian(value: bool) -> None:
    """Update the vegetarian preference."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE user_preferences SET vegetarian = %s", (int(value),))
            conn.commit()
