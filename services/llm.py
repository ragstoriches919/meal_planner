from __future__ import annotations

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
