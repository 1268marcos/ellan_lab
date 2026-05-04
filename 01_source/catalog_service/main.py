from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

import models  # noqa: F401
from database import Base, engine
from routers.categories import router as categories_router
from routers.products import partners_router, products_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="catalog-service", lifespan=lifespan)
app.include_router(partners_router, prefix="/api/v1")
app.include_router(products_router, prefix="/api/v1")
app.include_router(categories_router, prefix="/api/v1")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
