from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from db import inventories as inventories_db
from db import inventory as inv_db
from db import preferences as prefs_db
from routers.inventories import router as inventories_router
from routers.inventory import router as inventory_router
from routers.llm import router as llm_router
from routers.preferences import router as preferences_router

app = FastAPI(title="Meal Planner")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(inventories_router)
app.include_router(inventory_router)
app.include_router(llm_router)
app.include_router(preferences_router)


@app.get("/", include_in_schema=False)
def inventory_ui(request: Request):
    active_inventory_id = inventories_db.get_active_inventory_id() or 1
    items = inv_db.list_inventory(active_inventory_id)
    prefs = prefs_db.get_preferences()
    vegetarian = bool(prefs["vegetarian"]) if prefs else False
    all_inventories = inventories_db.list_inventories()
    return templates.TemplateResponse(
        request,
        "inventory.html",
        {
            "items": items,
            "vegetarian": vegetarian,
            "inventories": all_inventories,
            "active_inventory_id": active_inventory_id,
        },
    )
