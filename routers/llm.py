from __future__ import annotations

from fastapi import APIRouter, Query

from db import inventory as inv_db
from db import preferences as prefs_db
from services.llm import query_gemma, serialize_inventory

router = APIRouter(prefix="/llm", tags=["llm"])


@router.get("/chat")
def chat(q: str = Query(default="What meals can I make with what I have?")):
    items = inv_db.list_inventory()
    context = serialize_inventory(items)
    prefs = prefs_db.get_preferences()
    vegetarian = bool(prefs["vegetarian"]) if prefs else False
    answer = query_gemma(q, context, vegetarian=vegetarian)
    return {"question": q, "inventory_context": context, "answer": answer}
