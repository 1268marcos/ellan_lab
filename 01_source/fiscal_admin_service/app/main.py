from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import SessionLocal, init_db
from app.core.health import health_payload
from app.routers import fiscal_documents, fiscal_global_ops, fiscal_intelligence, fiscal_issuer_partners, fiscal_ops, seed
from app.services.seed_data import run_seed

API_PREFIX = "/api/v1/fiscal-admin"
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    if get_settings().seed_on_start:
        db = SessionLocal()
        try:
            run_seed(db)
        except Exception as exc:
            logger.warning("seed_on_start skipped (non-fatal): %s", exc)
            db.rollback()
        finally:
            db.close()
    yield


app = FastAPI(title="fiscal-admin-service", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(fiscal_issuer_partners.router, prefix=API_PREFIX)
app.include_router(fiscal_documents.router, prefix=API_PREFIX)
app.include_router(fiscal_ops.router, prefix=API_PREFIX)
app.include_router(fiscal_global_ops.router, prefix=API_PREFIX)
app.include_router(fiscal_intelligence.router, prefix=API_PREFIX)
app.include_router(seed.router, prefix=API_PREFIX)


@app.get("/health")
def health():
    return health_payload()


@app.get(f"{API_PREFIX}/health")
def health_v1():
    return health_payload()
