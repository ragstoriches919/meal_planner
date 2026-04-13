from fastapi import FastAPI

from routers.inventory import router as inventory_router

app = FastAPI(title="Meal Planner")

app.include_router(inventory_router)
