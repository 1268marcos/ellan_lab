from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import SessionLocal, init_db
from app.core.health import health_payload
from app.routers import (
    gateway_ops,
    locker_payment_methods,
    payment_interface_catalog,
    payment_method_catalog,
    payment_method_ui_alias,
    payment_provider_partners,
    seed,
)
from app.services.seed_data import run_seed

API_PREFIX = "/api/v1/payment-gateway-admin"


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


app = FastAPI(title="payment-gateway-admin-service", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(payment_method_catalog.router, prefix=API_PREFIX)
app.include_router(payment_interface_catalog.router, prefix=API_PREFIX)
app.include_router(payment_method_ui_alias.router, prefix=API_PREFIX)
app.include_router(locker_payment_methods.router, prefix=API_PREFIX)
app.include_router(payment_provider_partners.router, prefix=API_PREFIX)
app.include_router(gateway_ops.router, prefix=API_PREFIX)
app.include_router(seed.router, prefix=API_PREFIX)


@app.get("/health")
def health():
    return health_payload()


@app.get(f"{API_PREFIX}/health")
def health_v1():
    return health_payload()
