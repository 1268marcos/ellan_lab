# 01_source/backend/billing_fiscal_service/app/main.py
from fastapi import FastAPI

from app.api.routes_admin_fiscal import router as admin_fiscal_router
from app.api.routes_fiscal import router as fiscal_router
from app.api.routes_invoice import router as invoice_router
from app.core.db import init_db

app = FastAPI(title="Billing Fiscal Service")


@app.on_event("startup")
def startup():
    init_db()


app.include_router(invoice_router)
app.include_router(fiscal_router)
app.include_router(admin_fiscal_router)


@app.get("/health")
def health():
    return {"status": "ok"}