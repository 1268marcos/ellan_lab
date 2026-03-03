from app.routers.audit_snapshot import router as audit_snapshot_router
from app.routers.audit_self_check import router as audit_self_check_router
from app.core.db import init_db
from app.routers.audit import router as audit_router
from app.routers.debug import router as debug_router
from app.routers import catalog
from app.routers import locker_state
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
from app.routers import locker_state
from app.routers import allocations
from app.routers import hardware
import os
# import psycopg2
import redis
from app.core.db import get_conn
from app.services.mqtt_listener import start as start_mqtt_listener
from app.core.errors import http_exception_handler, unhandled_exception_handler

start_mqtt_listener()

app = FastAPI(
    title="ELLAN Backend SP (01_source/backend_sp/app/main.py)",
    version="1.0.0",
)

app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

@app.on_event("startup")
def startup():
    init_db()

app.include_router(audit_router)

app.include_router(debug_router)

app.include_router(audit_snapshot_router)

app.include_router(audit_self_check_router)

app.include_router(catalog.router)

app.include_router(locker_state.router)

app.include_router(allocations.router)

app.include_router(hardware.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_HOST = os.getenv("DB_HOST", "postgres_sp")
DB_NAME = os.getenv("DB_NAME", "locker_sp")
DB_USER = os.getenv("DB_USER", "admin")
DB_PASS = os.getenv("DB_PASS", "admin123")

@app.get("/")
def root():
    return {"message": "Locker SP Backend Running"}

@app.get("/health")
def health():
    try:
        # conn = psycopg2.connect(
        #     host=DB_HOST,
        #     database=DB_NAME,
        #     user=DB_USER,
        #     password=DB_PASS
        # )
        # conn.close()
        # return {"status": "connected to postgres"}
        #
        # Testa SQLite (Log Engine)
        conn = get_conn()
        conn.execute("SELECT 1;")
        return {"status": "ok", "db": "sqlite"}

    except Exception as e:
        # return {"error": str(e)}
        return {"status": "error", "detail": str(e)}

class Pagamento(BaseModel):
    metodo: str
    valor: float

@app.post("/debug/pagamento-mock")  # "/pagamento/" isso era errado
def processar_pagamento(pagamento: Pagamento):
    return {
        "regiao": "SP",
        "metodo": pagamento.metodo,
        "valor": pagamento.valor,
        "status": "aprovado"
    }
