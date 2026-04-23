from __future__ import annotations

import json
import re

import ollama

MODEL = "gemma4"


def serialize_inventory(items: list[dict]) -> str:
    """Format inventory rows into a compact, LLM-readable text block."""
    if not items:
        return "The pantry is currently empty."
    lines = []
    for item in items:
        qty = int(item["quantity"]) if item["quantity"] == int(item["quantity"]) else item["quantity"]
        unit = f" {item['unit']}" if item.get("unit") else ""
        lines.append(f"- {item['item_name']}: {qty}{unit}")
    return "Current pantry inventory:\n" + "\n".join(lines)


def query_gemma(prompt: str, inventory_context: str, vegetarian: bool = False) -> str:
    """Send a prompt to the local Gemma model with inventory injected as system context."""
    system_content = (
        "You are a helpful meal planning assistant. "
        "Use the following pantry inventory as context for your answers.\n\n"
        + inventory_context
    )
    if vegetarian:
        system_content += (
            "\n\nThe user is vegetarian. Only suggest vegetarian meals — "
            "no meat, poultry, or seafood."
        )
    response = ollama.chat(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": system_content,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )
    return response.message.content


def scan_receipt(image_bytes: bytes) -> list[dict]:
    """Send a receipt image to the vision model and return extracted grocery items."""
    prompt = (
        "You are a grocery receipt parser. Look at this receipt image and extract all food and grocery items. "
        "Return ONLY a JSON array — no other text, no markdown, no explanation. "
        'Format: [{"name": "eggs", "quantity": 12, "unit": "count"}, {"name": "milk", "quantity": 1, "unit": "gallon"}]. '
        "Use an empty string for unit if unknown. Use 1 for quantity if unclear. "
        "Only include actual food and grocery items, not fees, taxes, or store info."
    )
    response = ollama.chat(
        model=MODEL,
        messages=[{
            "role": "user",
            "content": prompt,
            "images": [image_bytes],
        }],
    )
    content = response.message.content.strip()
    # Strip markdown code fences if the model wrapped the JSON
    content = re.sub(r"^```(?:json)?\s*\n?", "", content)
    content = re.sub(r"\n?```\s*$", "", content)
    return json.loads(content.strip())
