from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import SessionLocal, init_db
from app.core.health import health_payload
from app.routers import (
    bi_core,
    bi_data_partners,
    bi_efficiency,
    bi_integrations,
    bi_ops,
    bi_players,
    bi_webhooks,
    integration_hub,
    seed,
)
from app.services.seed_data import run_seed

API_PREFIX = "/api/v1/analytics-bi-admin"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    if get_settings().seed_on_start:
        db = SessionLocal()
        try:
            run_seed(db)
        finally:
            db.close()
    yield


app = FastAPI(title="analytics-bi-admin-service", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(bi_core.router, prefix=API_PREFIX)
app.include_router(bi_data_partners.router, prefix=API_PREFIX)
app.include_router(bi_players.router, prefix=API_PREFIX)
app.include_router(bi_webhooks.router, prefix=API_PREFIX)
app.include_router(bi_ops.router, prefix=API_PREFIX)
app.include_router(bi_integrations.router, prefix=API_PREFIX)
app.include_router(bi_efficiency.router, prefix=API_PREFIX)
app.include_router(integration_hub.router, prefix=API_PREFIX)
app.include_router(seed.router, prefix=API_PREFIX)


@app.get("/health")
def health():
    return health_payload()


@app.get(f"{API_PREFIX}/health")
def health_v1():
    return health_payload()
