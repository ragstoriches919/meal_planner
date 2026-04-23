from __future__ import annotations

from db.connection import get_connection


def list_inventories() -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM inventories ORDER BY created_at")
            return cur.fetchall()


def create_inventory(name: str) -> dict:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO inventories (name) VALUES (%s)", (name,))
            conn.commit()
            cur.execute("SELECT * FROM inventories WHERE id = LAST_INSERT_ID()")
            return cur.fetchone()


def delete_inventory(inventory_id: int) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            rows = cur.execute("DELETE FROM inventories WHERE id = %s", (inventory_id,))
            conn.commit()
            return rows > 0


def get_active_inventory_id() -> int | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT active_inventory_id FROM user_preferences LIMIT 1")
            row = cur.fetchone()
            return row["active_inventory_id"] if row else None


def set_active_inventory(inventory_id: int) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE user_preferences SET active_inventory_id = %s",
                (inventory_id,),
            )
            conn.commit()
