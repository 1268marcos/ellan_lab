# 01_source/backend/billing_fiscal_service/app/main.py
from fastapi import FastAPI

from app.core.db import engine
from app.core.db_migrations import run_startup_migrations
from app.api.routes_invoice import router as invoice_router

app = FastAPI(title="Billing Fiscal Service")

@app.on_event("startup")
def startup():
    run_startup_migrations(engine)

app.include_router(invoice_router)


@app.get("/health")
def health():
    return {"status": "ok"}