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


@router.post("/recipes")
def get_recipes():
    items = inv_db.list_inventory()
    context = serialize_inventory(items)
    prefs = prefs_db.get_preferences()
    vegetarian = bool(prefs["vegetarian"]) if prefs else False
    raw = query_gemma(
        "List exactly 5 meals I can make with the pantry ingredients above. "
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
    items = inv_db.list_inventory()
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
