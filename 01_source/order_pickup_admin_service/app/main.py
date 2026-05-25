from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import SessionLocal, init_db
from app.core.health import health_payload
from app.routers import (
    credits,
    ecommerce_partners,
    fulfillment,
    integration_outbox,
    logistics_partners,
    orders,
    partner_integrations,
    pickup_lifecycle,
    pickups,
    seed,
    workers_ops,
)
from app.services.seed_data import run_seed

API_PREFIX = "/api/v1/order-pickup-admin"


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


app = FastAPI(title="order-pickup-admin-service", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ecommerce_partners.router, prefix=API_PREFIX)
app.include_router(logistics_partners.router, prefix=API_PREFIX)
app.include_router(partner_integrations.router, prefix=API_PREFIX)
app.include_router(orders.router, prefix=API_PREFIX)
app.include_router(pickups.router, prefix=API_PREFIX)
app.include_router(credits.router, prefix=API_PREFIX)
app.include_router(integration_outbox.router, prefix=API_PREFIX)
app.include_router(fulfillment.router, prefix=API_PREFIX)
app.include_router(pickup_lifecycle.router, prefix=API_PREFIX)
app.include_router(workers_ops.router, prefix=API_PREFIX)
app.include_router(seed.router, prefix=API_PREFIX)


@app.get("/health")
def health():
    return health_payload()


@app.get(f"{API_PREFIX}/health")
def health_v1():
    return health_payload()
