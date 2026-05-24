from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import SessionLocal, init_db
from app.core.health import health_payload
from app.routers import (
    currencies,
    fx_rates,
    integration_partners,
    payment_interface_catalog,
    payment_method_catalog,
    payment_method_ui_alias,
    advanced_ops,
    finance_sync,
    intelligence,
    professional,
    seed,
    wallet_providers,
)
from app.services.seed_data import run_seed

API_PREFIX = "/api/v1/money-cambio-admin"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    settings = get_settings()
    if settings.seed_on_start:
        db = SessionLocal()
        try:
            run_seed(db)
            if settings.finance_admin_sync_on_start and settings.finance_admin_sync_enabled:
                from app.services.finance_sync_service import sync_from_finance_admin

                try:
                    sync_from_finance_admin(db, trigger_finance_sync=True)
                except Exception:
                    pass  # Finance offline não impede subir Money
        finally:
            db.close()
    yield


app = FastAPI(title="money-cambio-admin-service", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(currencies.router, prefix=API_PREFIX)
app.include_router(payment_method_catalog.router, prefix=API_PREFIX)
app.include_router(payment_interface_catalog.router, prefix=API_PREFIX)
app.include_router(payment_method_ui_alias.router, prefix=API_PREFIX)
app.include_router(wallet_providers.router, prefix=API_PREFIX)
app.include_router(fx_rates.router, prefix=API_PREFIX)
app.include_router(integration_partners.router, prefix=API_PREFIX)
app.include_router(professional.router, prefix=API_PREFIX)
app.include_router(finance_sync.router, prefix=API_PREFIX)
app.include_router(intelligence.router, prefix=API_PREFIX)
app.include_router(advanced_ops.router, prefix=API_PREFIX)
app.include_router(seed.router, prefix=API_PREFIX)


@app.get("/health")
def health():
    return health_payload()


@app.get(f"{API_PREFIX}/health")
def health_v1():
    return health_payload()
