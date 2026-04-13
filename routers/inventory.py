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


@router.get("")
def list_inventory():
    return inv_db.list_inventory()


@router.post("", status_code=201)
def add_item(body: AddItemRequest):
    return inv_db.add_item(body.item_name, body.quantity, body.unit)


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
