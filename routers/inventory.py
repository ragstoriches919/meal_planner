from __future__ import annotations

from typing import Dict, List, Optional, Union

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from db import inventories as inventories_db
from db import inventory as inv_db
from db.connection import get_connection

router = APIRouter(prefix="/inventory", tags=["inventory"])


class AddItemRequest(BaseModel):
    item_name: str
    quantity: float
    unit: str = ""


class SubtractRequest(BaseModel):
    quantity: float


class BulkAddRequest(BaseModel):
    items: list[AddItemRequest]


class UpdateItemRequest(BaseModel):
    item_name: str
    quantity: float
    unit: str = ""
    category: str = ""


class BulkUpdateItem(BaseModel):
    id: int
    item_name: str
    quantity: float
    unit: str = ""
    category: str = ""


class BulkUpdateRequest(BaseModel):
    items: list[BulkUpdateItem]


class DictAddRequest(BaseModel):
    items: Dict[str, Union[float, List]]


def _resolve_inventory_id(inventory: Optional[str]) -> int:
    """Return the inventory id for the given name, or fall back to the active inventory."""
    if inventory:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id FROM inventories WHERE LOWER(name) = %s",
                    (inventory.lower(),),
                )
                row = cur.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail=f"Inventory '{inventory}' not found.")
        return row["id"]
    inv_id = inventories_db.get_active_inventory_id()
    if inv_id is None:
        raise HTTPException(status_code=400, detail="No active inventory. Create one first.")
    return inv_id


@router.get("")
def list_inventory(inventory: Optional[str] = Query(default=None)):
    return inv_db.list_inventory(_resolve_inventory_id(inventory))


@router.post("", status_code=201)
def add_item(body: AddItemRequest, inventory: Optional[str] = Query(default=None)):
    return inv_db.add_item(body.item_name, body.quantity, body.unit, _resolve_inventory_id(inventory))


@router.post("/bulk", status_code=201)
def bulk_add_items(body: BulkAddRequest, inventory: Optional[str] = Query(default=None)):
    inv_id = _resolve_inventory_id(inventory)
    return [inv_db.add_item(item.item_name, item.quantity, item.unit, inv_id) for item in body.items]


@router.post("/from-dict", status_code=201)
def add_items_from_dict(body: DictAddRequest, inventory: Optional[str] = Query(default=None)):
    return inv_db.add_items_from_dict(body.items, _resolve_inventory_id(inventory))


@router.put("/bulk")
def bulk_update_items(body: BulkUpdateRequest):
    results = []
    for item in body.items:
        row = inv_db.get_item_by_id(item.id)
        if row is None:
            raise HTTPException(status_code=404, detail=f"Item {item.id} not found.")
        results.append(inv_db.update_item(item.id, item.item_name, item.quantity, item.unit, item.category))
    return results


@router.put("/{item_id}")
def update_item(item_id: int, body: UpdateItemRequest):
    row = inv_db.get_item_by_id(item_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found.")
    return inv_db.update_item(item_id, body.item_name, body.quantity, body.unit, body.category)


@router.patch("/{item_id}")
def subtract_item(item_id: int, body: SubtractRequest):
    row = inv_db.get_item_by_id(item_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found.")
    try:
        return inv_db.subtract_item(item_id, body.quantity)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/{item_id}", status_code=204)
def remove_item(item_id: int):
    row = inv_db.get_item_by_id(item_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found.")
    inv_db.remove_item(item_id)
