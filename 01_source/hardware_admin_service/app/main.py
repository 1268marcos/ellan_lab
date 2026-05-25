from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import SessionLocal, init_db
from app.core.health import health_payload
from app.routers import cross_domain, hardware_assets, hardware_vendors, integration_hub, locker_finance_topology, locker_operators, professional_ops, runtime_lockers, seed
from app.routers.runtime_lockers import hardware_ops_router
from app.services.seed_data import run_seed

API_PREFIX = "/api/v1/hardware-admin"


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


app = FastAPI(title="hardware-admin-service", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(hardware_vendors.router, prefix=API_PREFIX)
app.include_router(hardware_assets.router, prefix=API_PREFIX)
app.include_router(locker_operators.router, prefix=API_PREFIX)
app.include_router(runtime_lockers.router, prefix=API_PREFIX)
app.include_router(hardware_ops_router, prefix=API_PREFIX)
app.include_router(cross_domain.router, prefix=API_PREFIX)
app.include_router(integration_hub.router, prefix=API_PREFIX)
app.include_router(professional_ops.router, prefix=API_PREFIX)
app.include_router(locker_finance_topology.router, prefix=API_PREFIX)
app.include_router(seed.router, prefix=API_PREFIX)


@app.get("/health")
def health():
    return health_payload()


@app.get(f"{API_PREFIX}/health")
def health_v1():
    return health_payload()
