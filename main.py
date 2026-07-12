from fastapi import FastAPI

from app.routers.credits import router as credits_router
from app.routers.resources import all_resource_routers

app = FastAPI(
    title="Intelligent Document Engine API",
    description="CRUD API over the multi-tenant document + credits schema.",
    version="0.1.0",
)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}


for router in all_resource_routers:
    app.include_router(router)

app.include_router(credits_router)
