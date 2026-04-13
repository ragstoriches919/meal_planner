from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from db import inventory as inv_db
from routers.inventory import router as inventory_router

app = FastAPI(title="Meal Planner")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(inventory_router)


@app.get("/", include_in_schema=False)
def inventory_ui(request: Request):
    items = inv_db.list_inventory()
    return templates.TemplateResponse("inventory.html", {"request": request, "items": items})
