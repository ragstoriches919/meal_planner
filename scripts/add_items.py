"""
Add items to inventory by passing a JSON dict on the command line.

Usage:
    uv run scripts/add_items.py '<json_dict>'

Values can be a plain number or a [quantity, unit] list.

Examples:
    uv run scripts/add_items.py '{"eggs": 12}'
    uv run scripts/add_items.py '{"milk": [1, "gallon"], "butter": [2, "sticks"], "flour": 5}'
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from db.inventory import add_items_from_dict


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    try:
        items = json.loads(sys.argv[1])
    except json.JSONDecodeError as e:
        print(f"Invalid JSON: {e}")
        sys.exit(1)

    if not isinstance(items, dict):
        print("Input must be a JSON object, e.g. {\"eggs\": 12}")
        sys.exit(1)

    results = add_items_from_dict(items)
    for row in results:
        unit = f" {row['unit']}" if row.get("unit") else ""
        print(f"  {row['item_name']}: {row['quantity']}{unit}")
    print(f"\n{len(results)} item(s) added/updated.")
