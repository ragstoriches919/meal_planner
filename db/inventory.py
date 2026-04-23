from __future__ import annotations

from db.connection import get_connection


def add_item(name: str, quantity: float, unit: str = "") -> dict:
    """Insert a new inventory row or increment quantity if the item already exists."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO inventory (item_name, quantity, unit)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    quantity = quantity + VALUES(quantity),
                    unit     = VALUES(unit)
                """,
                (name, quantity, unit),
            )
            conn.commit()
            cur.execute(
                "SELECT * FROM inventory WHERE item_name = %s", (name,)
            )
            return cur.fetchone()


def subtract_item(name: str, quantity: float) -> dict:
    """Decrement quantity for an inventory item. Raises ValueError if it would go negative."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, quantity FROM inventory WHERE item_name = %s", (name,)
            )
            row = cur.fetchone()
            if row is None:
                raise ValueError(f"Item '{name}' not found in inventory.")
            new_qty = float(row["quantity"]) - quantity
            if new_qty < 0:
                raise ValueError(
                    f"Subtracting {quantity} from '{name}' (current: {row['quantity']}) "
                    "would result in a negative quantity."
                )
            cur.execute(
                "UPDATE inventory SET quantity = %s WHERE item_name = %s",
                (new_qty, name),
            )
            conn.commit()
            cur.execute(
                "SELECT * FROM inventory WHERE item_name = %s", (name,)
            )
            return cur.fetchone()


def remove_item(name: str) -> bool:
    """Delete an inventory item by name. Returns True if a row was deleted."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            rows_affected = cur.execute(
                "DELETE FROM inventory WHERE item_name = %s", (name,)
            )
            conn.commit()
            return rows_affected > 0


def list_inventory() -> list[dict]:
    """Return all rows in the inventory table."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM inventory ORDER BY item_name")
            return cur.fetchall()


def get_item_by_id(item_id: int) -> dict | None:
    """Fetch a single inventory row by primary key."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM inventory WHERE id = %s", (item_id,))
            return cur.fetchone()


def add_items_from_dict(items: dict) -> list[dict]:
    """Add multiple items from a dict.

    Each key is an item name. Values can be:
      - a number:          {"eggs": 12}
      - a (qty, unit) tuple/list: {"milk": (1, "gallon")}
    """
    results = []
    for name, value in items.items():
        if isinstance(value, (list, tuple)):
            quantity, unit = float(value[0]), str(value[1]) if len(value) > 1 else ""
        else:
            quantity, unit = float(value), ""
        results.append(add_item(name, quantity, unit))
    return results
