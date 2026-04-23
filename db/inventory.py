from __future__ import annotations

from db.connection import get_connection


def list_inventory(inventory_id: int) -> list[dict]:
    """Return all rows in the inventory table for the given inventory."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM inventory WHERE inventory_id = %s ORDER BY item_name",
                (inventory_id,),
            )
            return cur.fetchall()


def add_item(name: str, quantity: float, unit: str = "", inventory_id: int = 1) -> dict:
    """Insert a new inventory row or increment quantity if the item already exists."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO inventory (inventory_id, item_name, quantity, unit)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    quantity = quantity + VALUES(quantity),
                    unit     = VALUES(unit)
                """,
                (inventory_id, name, quantity, unit),
            )
            conn.commit()
            cur.execute(
                "SELECT * FROM inventory WHERE inventory_id = %s AND item_name = %s",
                (inventory_id, name),
            )
            return cur.fetchone()


def subtract_item(item_id: int, quantity: float) -> dict:
    """Decrement quantity for an inventory item by primary key. Raises ValueError if negative."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, item_name, quantity FROM inventory WHERE id = %s", (item_id,))
            row = cur.fetchone()
            if row is None:
                raise ValueError(f"Item id {item_id} not found in inventory.")
            new_qty = float(row["quantity"]) - quantity
            if new_qty < 0:
                raise ValueError(
                    f"Subtracting {quantity} from '{row['item_name']}' "
                    f"(current: {row['quantity']}) would result in a negative quantity."
                )
            cur.execute("UPDATE inventory SET quantity = %s WHERE id = %s", (new_qty, item_id))
            conn.commit()
            cur.execute("SELECT * FROM inventory WHERE id = %s", (item_id,))
            return cur.fetchone()


def remove_item(item_id: int) -> bool:
    """Delete an inventory item by primary key. Returns True if a row was deleted."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            rows_affected = cur.execute("DELETE FROM inventory WHERE id = %s", (item_id,))
            conn.commit()
            return rows_affected > 0


def update_item(item_id: int, item_name: str, quantity: float, unit: str = "") -> dict:
    """Update an existing inventory row by primary key."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE inventory SET item_name = %s, quantity = %s, unit = %s WHERE id = %s",
                (item_name, quantity, unit, item_id),
            )
            conn.commit()
            cur.execute("SELECT * FROM inventory WHERE id = %s", (item_id,))
            return cur.fetchone()


def get_item_by_id(item_id: int) -> dict | None:
    """Fetch a single inventory row by primary key."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM inventory WHERE id = %s", (item_id,))
            return cur.fetchone()


def add_items_from_dict(items: dict, inventory_id: int = 1) -> list[dict]:
    """Add multiple items from a dict.

    Each key is an item name. Values can be:
      - a number:                  {"eggs": 12}
      - a (qty, unit) tuple/list:  {"milk": (1, "gallon")}
    """
    results = []
    for name, value in items.items():
        if isinstance(value, (list, tuple)):
            quantity, unit = float(value[0]), str(value[1]) if len(value) > 1 else ""
        else:
            quantity, unit = float(value), ""
        results.append(add_item(name, quantity, unit, inventory_id))
    return results
