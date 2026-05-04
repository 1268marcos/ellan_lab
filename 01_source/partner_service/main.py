from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

import models  # noqa: F401
from database import Base, engine
from routers.partners import router as partners_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="partner-service", lifespan=lifespan)
app.include_router(partners_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
