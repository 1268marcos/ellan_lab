from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import init_db
from app.core.health import health_payload
from app.routers import api_keys, lockers, webhooks

API_PREFIX = "/api/v1/locker-create"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="locker-create-service", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(lockers.router, prefix=API_PREFIX)
app.include_router(webhooks.router, prefix=API_PREFIX)
app.include_router(api_keys.router, prefix=API_PREFIX)


@app.get("/health")
def health():
    return health_payload()


@app.get(f"{API_PREFIX}/health")
def health_v1():
    return health_payload()
