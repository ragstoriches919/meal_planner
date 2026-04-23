from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from db import inventories as inv_db

router = APIRouter(prefix="/inventories", tags=["inventories"])


class CreateInventoryRequest(BaseModel):
    name: str


@router.get("")
def list_inventories():
    return inv_db.list_inventories()


@router.post("", status_code=201)
def create_inventory(body: CreateInventoryRequest):
    return inv_db.create_inventory(body.name)


@router.delete("/{inventory_id}", status_code=204)
def delete_inventory(inventory_id: int):
    active_id = inv_db.get_active_inventory_id()
    if inventory_id == active_id:
        raise HTTPException(status_code=400, detail="Cannot delete the active inventory.")
    if not inv_db.delete_inventory(inventory_id):
        raise HTTPException(status_code=404, detail=f"Inventory {inventory_id} not found.")


@router.post("/{inventory_id}/activate")
def activate_inventory(inventory_id: int):
    inventories = inv_db.list_inventories()
    if not any(i["id"] == inventory_id for i in inventories):
        raise HTTPException(status_code=404, detail=f"Inventory {inventory_id} not found.")
    inv_db.set_active_inventory(inventory_id)
    return {"active_inventory_id": inventory_id}
