from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import SessionLocal, init_db
from app.core.scheduler import start_finance_scheduler, stop_finance_scheduler
from app.core.health import health_payload
from app.routers import advanced, billing, catalog, extended, intelligence, jobs, partners, revenue, seed, wallet
from app.services.seed_data import run_seed

API_PREFIX = "/api/v1/finance-admin"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    if get_settings().seed_on_start:
        db = SessionLocal()
        try:
            run_seed(db)
        finally:
            db.close()
    start_finance_scheduler()
    yield
    stop_finance_scheduler()


app = FastAPI(title="finance-admin-service", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(partners.router, prefix=API_PREFIX)
app.include_router(billing.router, prefix=API_PREFIX)
app.include_router(wallet.router, prefix=API_PREFIX)
app.include_router(extended.router, prefix=API_PREFIX)
app.include_router(catalog.router, prefix=API_PREFIX)
app.include_router(intelligence.router, prefix=API_PREFIX)
app.include_router(advanced.router, prefix=API_PREFIX)
app.include_router(revenue.router, prefix=API_PREFIX)
app.include_router(jobs.router, prefix=API_PREFIX)
app.include_router(seed.router, prefix=API_PREFIX)


@app.get("/health")
def health():
    return health_payload()


@app.get(f"{API_PREFIX}/health")
def health_v1():
    return health_payload()
