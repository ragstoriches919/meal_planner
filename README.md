# Meal Planner

A weekly meal planner with pantry inventory tracking and LLM-powered recipe suggestions.

## Starting the app

```bash
uv run uvicorn main:app --reload
```

Open `http://localhost:8000`.

---

## Inventory

### Web UI

The inventory page lets you manage items directly in the browser.

**Edit an item** — click any cell in the Item, Qty, or Unit columns to edit it inline. Press Enter or click away to save. Press Escape to cancel.

**Delete an item** — hover over a row to reveal the ✕ button on the right.

**Add an item** — use the input row at the bottom of the table. Fill in the name, quantity, and unit, then press Enter or click **+ Add**.

---

### API endpoints

All endpoints operate on the currently active inventory.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/inventory` | List all items |
| `POST` | `/inventory` | Add a single item |
| `POST` | `/inventory/bulk` | Add multiple items (list format) |
| `POST` | `/inventory/from-dict` | Add multiple items (dict format) |
| `PUT` | `/inventory/{id}` | Update an item |
| `PATCH` | `/inventory/{id}` | Subtract quantity from an item |
| `DELETE` | `/inventory/{id}` | Delete an item |

All write endpoints accept an `?inventory=` query parameter (`srida` or `raghu`). This is required — always specify which inventory you're adding to.

**Add a single item:**
```bash
curl -X POST "http://localhost:8000/inventory?inventory=srida" \
  -H "Content-Type: application/json" \
  -d '{"item_name": "eggs", "quantity": 12, "unit": "count"}'
```

**Add multiple items (bulk list):**
```bash
curl -X POST "http://localhost:8000/inventory/bulk?inventory=raghu" \
  -H "Content-Type: application/json" \
  -d '{"items": [
    {"item_name": "milk", "quantity": 1, "unit": "gallon"},
    {"item_name": "butter", "quantity": 2, "unit": "sticks"}
  ]}'
```

**Add multiple items (dict format):**
```bash
curl -X POST "http://localhost:8000/inventory/from-dict?inventory=srida" \
  -H "Content-Type: application/json" \
  -d '{"items": {"eggs": 12, "milk": [1, "gallon"], "flour": 5}}'
```

Values can be a plain number (no unit) or a `[quantity, unit]` pair.

**List items for a specific inventory:**
```bash
curl "http://localhost:8000/inventory?inventory=raghu"
```

---

### Command-line script

`scripts/add_items.py` lets you seed inventory from the terminal without curl. Pass a JSON dict as the first argument and specify the target inventory with `--srida` or `--raghu` (required):

```bash
uv run scripts/add_items.py '{"eggs": 12}' --srida
uv run scripts/add_items.py '{"milk": [1, "gallon"], "butter": [2, "sticks"], "flour": 5}' --raghu
```

The `--srida` or `--raghu` flag is mandatory — the script will exit with an error if neither is provided. Values can be a plain number (no unit) or a `[quantity, unit]` pair.

---

## Multiple inventories

The app supports multiple named inventories. Switch between them using the dropdown in the top-right of the header.

### Web UI

- **Switch** — select an inventory from the dropdown; the page reloads showing that inventory's items.
- **Create** — click the **+** button next to the dropdown, enter a name, and the new inventory becomes active immediately.

### API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/inventories` | List all inventories |
| `POST` | `/inventories` | Create a new inventory |
| `POST` | `/inventories/{id}/activate` | Set the active inventory |
| `DELETE` | `/inventories/{id}` | Delete an inventory (cannot delete the active one) |

**Create an inventory:**
```bash
curl -X POST http://localhost:8000/inventories \
  -H "Content-Type: application/json" \
  -d '{"name": "Pantry"}'
```

**Switch active inventory:**
```bash
curl -X POST http://localhost:8000/inventories/3/activate
```

---

## Database setup

Run once to create or migrate all tables:

```bash
uv run python -m db.init_db
```

Safe to re-run on an existing database — applies migrations without data loss.
