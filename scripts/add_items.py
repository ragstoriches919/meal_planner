"""
Add items to inventory by passing a JSON dict on the command line.

Usage:
    uv run scripts/add_items.py '<json_dict>' --srida
    uv run scripts/add_items.py '<json_dict>' --raghu

The --srida or --raghu flag is required and selects which inventory to add to.
Values can be a plain number or a [quantity, unit] list.

Examples:
    uv run scripts/add_items.py '{"eggs": 12}' --srida
    uv run scripts/add_items.py '{"milk": [1, "gallon"], "butter": [2, "sticks"]}' --raghu
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from db.connection import get_connection
from db.inventory import add_items_from_dict


def get_inventory_id_by_name(name: str) -> int:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM inventories WHERE LOWER(name) = %s", (name.lower(),))
            row = cur.fetchone()
            if row is None:
                print(f"Error: inventory '{name}' not found.")
                sys.exit(1)
            return row["id"]


if __name__ == "__main__":
    args = sys.argv[1:]

    inventory_name = None
    if "--srida" in args:
        inventory_name = "srida"
        args = [a for a in args if a != "--srida"]
    elif "--raghu" in args:
        inventory_name = "raghu"
        args = [a for a in args if a != "--raghu"]

    if not inventory_name:
        print("Error: --srida or --raghu is required.\n")
        print(__doc__)
        sys.exit(1)

    if not args:
        print(__doc__)
        sys.exit(1)

    try:
        items = json.loads(args[0])
    except json.JSONDecodeError as e:
        print(f"Invalid JSON: {e}")
        sys.exit(1)

    if not isinstance(items, dict):
        print('Input must be a JSON object, e.g. {"eggs": 12}')
        sys.exit(1)

    inventory_id = get_inventory_id_by_name(inventory_name)
    results = add_items_from_dict(items, inventory_id)
    for row in results:
        unit = f" {row['unit']}" if row.get("unit") else ""
        print(f"  {row['item_name']}: {row['quantity']}{unit}")
    print(f"\n{len(results)} item(s) added/updated.")
