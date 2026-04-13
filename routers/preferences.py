from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from db import preferences as prefs_db

router = APIRouter(prefix="/preferences", tags=["preferences"])


class PreferencesUpdate(BaseModel):
    vegetarian: bool


@router.get("")
def get_preferences():
    row = prefs_db.get_preferences()
    return {"vegetarian": bool(row["vegetarian"])}


@router.patch("")
def update_preferences(body: PreferencesUpdate):
    prefs_db.set_vegetarian(body.vegetarian)
    return {"vegetarian": body.vegetarian}
