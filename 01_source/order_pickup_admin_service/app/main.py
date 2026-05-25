from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import SessionLocal, init_db
from app.core.health import health_payload
from app.routers import (
    allocations,
    credits,
    ecommerce_partners,
    fulfillment,
    food_delivery_orders,
    fulfillment_orders,
    integration_outbox,
    logistics_manifests,
    logistics_partners,
    omnichannel_orders,
    order_channels,
    order_commissions,
    order_items_crud,
    order_lifecycle_ops,
    orders,
    orders_advanced,
    orders_extras,
    orders_hub,
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
app.include_router(orders_hub.router, prefix=API_PREFIX)
app.include_router(orders_extras.router, prefix=API_PREFIX)
app.include_router(orders_advanced.router, prefix=API_PREFIX)
app.include_router(allocations.router, prefix=API_PREFIX)
app.include_router(logistics_manifests.router, prefix=API_PREFIX)
app.include_router(order_channels.router, prefix=API_PREFIX)
app.include_router(order_commissions.router, prefix=API_PREFIX)
app.include_router(order_items_crud.router, prefix=API_PREFIX)
app.include_router(order_lifecycle_ops.router, prefix=API_PREFIX)
app.include_router(pickups.router, prefix=API_PREFIX)
app.include_router(credits.router, prefix=API_PREFIX)
app.include_router(integration_outbox.router, prefix=API_PREFIX)
app.include_router(fulfillment.router, prefix=API_PREFIX)
app.include_router(omnichannel_orders.router, prefix=API_PREFIX)
app.include_router(fulfillment_orders.router, prefix=API_PREFIX)
app.include_router(food_delivery_orders.router, prefix=API_PREFIX)
app.include_router(pickup_lifecycle.router, prefix=API_PREFIX)
app.include_router(workers_ops.router, prefix=API_PREFIX)
app.include_router(seed.router, prefix=API_PREFIX)


@app.get("/health")
def health():
    return health_payload()


@app.get(f"{API_PREFIX}/health")
def health_v1():
    return health_payload()
