from __future__ import annotations

from typing import Dict, List, Union

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from db import inventory as inv_db

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


class DictAddRequest(BaseModel):
    items: Dict[str, Union[float, List]]


@router.get("")
def list_inventory():
    return inv_db.list_inventory()


@router.post("", status_code=201)
def add_item(body: AddItemRequest):
    return inv_db.add_item(body.item_name, body.quantity, body.unit)


@router.post("/bulk", status_code=201)
def bulk_add_items(body: BulkAddRequest):
    return [inv_db.add_item(item.item_name, item.quantity, item.unit) for item in body.items]


@router.post("/from-dict", status_code=201)
def add_items_from_dict(body: DictAddRequest):
    return inv_db.add_items_from_dict(body.items)


@router.put("/{item_id}")
def update_item(item_id: int, body: UpdateItemRequest):
    row = inv_db.get_item_by_id(item_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found.")
    return inv_db.update_item(item_id, body.item_name, body.quantity, body.unit)


@router.patch("/{item_id}")
def subtract_item(item_id: int, body: SubtractRequest):
    row = inv_db.get_item_by_id(item_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found.")
    try:
        return inv_db.subtract_item(row["item_name"], body.quantity)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/{item_id}", status_code=204)
def remove_item(item_id: int):
    row = inv_db.get_item_by_id(item_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found.")
    inv_db.remove_item(row["item_name"])
