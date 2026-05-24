from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import SessionLocal, init_db
from app.core.health import health_payload
from app.routers import (
    ecosystem_players,
    ecosystem_segments,
    gateway_events,
    cross_domain_hub,
    integration_incidents,
    integration_milestones,
    intelligence,
    order_context,
    partner_holds,
    player_compliance,
    player_country_coverage,
    player_integrations,
    player_relations,
    payment_instructions,
    payment_splits,
    payment_transactions,
    payments,
    reconciliation_batches,
    routing_rules,
    saved_methods,
    settlement_corridors,
    seed,
    webhook_deliveries,
    webhook_endpoints,
)
from app.services.seed_data import run_seed

API_PREFIX = "/api/v1/payments-admin"


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


app = FastAPI(title="payments-admin-service", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(payment_transactions.router, prefix=API_PREFIX)
app.include_router(payment_instructions.router, prefix=API_PREFIX)
app.include_router(payment_splits.router, prefix=API_PREFIX)
app.include_router(payments.router, prefix=API_PREFIX)
app.include_router(webhook_endpoints.router, prefix=API_PREFIX)
app.include_router(gateway_events.router, prefix=API_PREFIX)
app.include_router(ecosystem_players.router, prefix=API_PREFIX)
app.include_router(ecosystem_segments.router, prefix=API_PREFIX)
app.include_router(player_integrations.router, prefix=API_PREFIX)
app.include_router(player_country_coverage.router, prefix=API_PREFIX)
app.include_router(player_relations.router, prefix=API_PREFIX)
app.include_router(order_context.router, prefix=API_PREFIX)
app.include_router(reconciliation_batches.router, prefix=API_PREFIX)
app.include_router(webhook_deliveries.router, prefix=API_PREFIX)
app.include_router(partner_holds.router, prefix=API_PREFIX)
app.include_router(saved_methods.router, prefix=API_PREFIX)
app.include_router(integration_milestones.router, prefix=API_PREFIX)
app.include_router(settlement_corridors.router, prefix=API_PREFIX)
app.include_router(player_compliance.router, prefix=API_PREFIX)
app.include_router(routing_rules.router, prefix=API_PREFIX)
app.include_router(integration_incidents.router, prefix=API_PREFIX)
app.include_router(cross_domain_hub.router, prefix=API_PREFIX)
app.include_router(intelligence.router, prefix=API_PREFIX)
app.include_router(seed.router, prefix=API_PREFIX)


@app.get("/health")
def health():
    return health_payload()


@app.get(f"{API_PREFIX}/health")
def health_v1():
    return health_payload()
