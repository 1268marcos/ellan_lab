from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import SessionLocal, init_db
from app.core.health import health_payload
from app.routers import (
    ml_data_partners,
    ml_features,
    ml_feedback,
    ml_model_metadata,
    ml_network_players,
    ml_readiness,
    ml_ops,
    ml_predictions,
    seed,
)
from app.services.seed_data import run_seed

API_PREFIX = "/api/v1/ml-admin"


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


app = FastAPI(title="ml-admin-service", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ml_data_partners.router, prefix=API_PREFIX)
app.include_router(ml_model_metadata.router, prefix=API_PREFIX)
app.include_router(ml_features.router, prefix=API_PREFIX)
app.include_router(ml_predictions.router, prefix=API_PREFIX)
app.include_router(ml_feedback.router, prefix=API_PREFIX)
app.include_router(ml_ops.router, prefix=API_PREFIX)
app.include_router(ml_network_players.router, prefix=API_PREFIX)
app.include_router(ml_readiness.router, prefix=API_PREFIX)
app.include_router(seed.router, prefix=API_PREFIX)


@app.get("/health")
def health():
    return health_payload()


@app.get(f"{API_PREFIX}/health")
def health_v1():
    return health_payload()
