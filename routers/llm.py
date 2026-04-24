from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from pydantic import BaseModel

from db import inventories as inventories_db
from db import inventory as inv_db
from db import preferences as prefs_db
from services.llm import query_gemma, scan_receipt, serialize_inventory
from services.pdf_email import send_recipe_email

router = APIRouter(prefix="/llm", tags=["llm"])


class RecipeHintRequest(BaseModel):
    hint: str = ""


class EmailRecipeRequest(BaseModel):
    recipe: str


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


@router.post("/scan-receipt")
async def scan_receipt_endpoint(file: UploadFile = File(...)):
    """Extract items from a receipt image and return them for user confirmation — does not add to inventory."""
    image_bytes = await file.read()
    items = scan_receipt(image_bytes)
    cleaned = []
    for item in items:
        name = str(item.get("name", "")).strip()
        if not name:
            continue
        cleaned.append({
            "name": name,
            "quantity": float(item.get("quantity", 1) or 1),
            "unit": str(item.get("unit", "") or ""),
        })
    return {"items": cleaned}


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


@router.post("/recipe/{name}/email")
def email_recipe(name: str, body: EmailRecipeRequest):
    try:
        send_recipe_email(name, body.recipe)
        return {"success": True}
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {e}")
