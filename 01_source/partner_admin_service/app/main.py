from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import SessionLocal, init_db
from app.core.health import health_payload
from app.routers import (
    ecommerce_partners,
    logistics_partners,
    partner_domain,
    capability_webhooks,
    partner_ecosystem,
    partner_global_ops,
    partner_integrations,
    partner_ops,
    seed,
    tenants,
    security_admin,
    security_cross_ops,
    security_value,
    user_roles,
    users,
    critical_audit,
    critical_table_security,
)
from app.services.seed_data import run_seed

API_PREFIX = "/api/v1/partner-admin"


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


app = FastAPI(title="partner-admin-service", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ecommerce_partners.router, prefix=API_PREFIX)
app.include_router(logistics_partners.router, prefix=API_PREFIX)
app.include_router(users.router, prefix=API_PREFIX)
app.include_router(critical_audit.router, prefix=API_PREFIX)
app.include_router(critical_table_security.router, prefix=API_PREFIX)
app.include_router(user_roles.router, prefix=API_PREFIX)
app.include_router(security_admin.router, prefix=API_PREFIX)
app.include_router(security_cross_ops.router, prefix=API_PREFIX)
app.include_router(security_value.router, prefix=API_PREFIX)
app.include_router(partner_integrations.router, prefix=API_PREFIX)
app.include_router(partner_ops.ops_router, prefix=API_PREFIX)
app.include_router(partner_ops.stores_router, prefix=API_PREFIX)
app.include_router(partner_domain.router, prefix=API_PREFIX)
app.include_router(partner_ecosystem.players_router, prefix=API_PREFIX)
app.include_router(partner_ecosystem.router, prefix=API_PREFIX)
app.include_router(partner_global_ops.router, prefix=API_PREFIX)
app.include_router(capability_webhooks.router, prefix=API_PREFIX)
app.include_router(capability_webhooks.ingress_router, prefix=API_PREFIX)
app.include_router(tenants.router, prefix=API_PREFIX)
app.include_router(seed.router, prefix=API_PREFIX)


@app.get("/health")
def health():
    return health_payload()


@app.get(f"{API_PREFIX}/health")
def health_v1():
    return health_payload()
