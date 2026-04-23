from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from db import inventories as inventories_db
from db import inventory as inv_db
from db import preferences as prefs_db
from services.llm import query_gemma, serialize_inventory

router = APIRouter(prefix="/llm", tags=["llm"])


class RecipeHintRequest(BaseModel):
    hint: str = ""


@router.get("/chat")
def chat(q: str = Query(default="What meals can I make with what I have?")):
    inv_id = inventories_db.get_active_inventory_id() or 1
    items = inv_db.list_inventory(inv_id)
    context = serialize_inventory(items)
    prefs = prefs_db.get_preferences()
    vegetarian = bool(prefs["vegetarian"]) if prefs else False
    answer = query_gemma(q, context, vegetarian=vegetarian)
    return {"question": q, "inventory_context": context, "answer": answer}


@router.post("/recipes")
def get_recipes(body: RecipeHintRequest = RecipeHintRequest()):
    inv_id = inventories_db.get_active_inventory_id() or 1
    items = inv_db.list_inventory(inv_id)
    context = serialize_inventory(items)
    prefs = prefs_db.get_preferences()
    vegetarian = bool(prefs["vegetarian"]) if prefs else False
    hint_clause = f'Focus suggestions around: "{body.hint}". ' if body.hint.strip() else ""
    raw = query_gemma(
        f"{hint_clause}List exactly 5 meals I can make with the pantry ingredients above. "
        "Reply with only the meal names, one per line, no numbers, no punctuation, no extra text.",
        context,
        vegetarian=vegetarian,
    )
    recipes = [
        line.strip().lstrip("•-*123456789. ")
        for line in raw.strip().splitlines()
        if line.strip()
    ][:5]
    return {"recipes": recipes, "vegetarian": vegetarian}


@router.post("/recipe/{name}")
def get_recipe(name: str):
    inv_id = inventories_db.get_active_inventory_id() or 1
    items = inv_db.list_inventory(inv_id)
    context = serialize_inventory(items)
    prefs = prefs_db.get_preferences()
    vegetarian = bool(prefs["vegetarian"]) if prefs else False
    recipe = query_gemma(
        f'Write the complete recipe for "{name}". '
        "Include an Ingredients section with quantities and a Steps section with numbered instructions. Be practical and concise.",
        context,
        vegetarian=vegetarian,
    )
    return {"name": name, "recipe": recipe}
