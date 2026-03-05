import asyncio
import logging
import os 
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fastapi import Request
from fastapi.responses import JSONResponse
import traceback, time

from app.health.health import router as health_router
from app.health.internal import router as internal_router
from app.core.version import get_version

from app.core.db import SessionLocal
from app.core.db import init_db
from app.jobs.expiry import run_expiry_once
from app.routers import orders, kiosk, pickup, internal

from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, DateTime, Float, Boolean
import datetime

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger("order_pickup_service")

EXPIRY_POLL_SEC = int(os.getenv("EXPIRY_POLL_SEC", "60"))



# Função de inicialização do banco
def init_database():
    """Cria as tabelas se não existirem"""
    database_url = os.getenv('DATABASE_URL', 'sqlite:////data/sqlite/order_pickup/orders.db')
    
    logger.info(f"Inicializando banco de dados: {database_url}")
    
    # Para SQLite, garantir diretório
    if database_url.startswith('sqlite'):
        db_path = database_url.replace('sqlite:///', '')
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    engine = create_engine(database_url)
    
    # Definir tabelas (use suas classes SQLAlchemy reais aqui)
    # Este é um exemplo - ajuste conforme seu modelo real
    metadata = MetaData()
    
    orders = Table(
        'orders', metadata,
        Column('id', String(50), primary_key=True),
        Column('user_id', String(50), nullable=True),
        Column('channel', String(20), nullable=False),
        Column('region', String(10), nullable=False),
        Column('totem_id', String(50), nullable=False),
        Column('sku_id', String(50), nullable=False),
        Column('amount_cents', Integer, nullable=False),
        Column('status', String(50), nullable=False),
        Column('gateway_transaction_id', String(100), nullable=True),
        Column('paid_at', DateTime, nullable=True),
        Column('pickup_deadline_at', DateTime, nullable=True),
        Column('guest_session_id', String(100), nullable=True),
        Column('receipt_email', String(255), nullable=True),
        Column('receipt_phone', String(50), nullable=True),
        Column('consent_marketing', Boolean, default=False),
        Column('guest_phone', String(50), nullable=True),
        Column('guest_email', String(255), nullable=True),
        Column('created_at', DateTime, default=datetime.datetime.utcnow),
    )
    
    # Criar tabelas
    metadata.create_all(engine)
    logger.info("Tabelas verificadas/criadas com sucesso")
    
    return engine




# app = FastAPI()
app = FastAPI(
    # title="Minha API (01_source/order_pickup_service/app/main.py)",
    title="ELLAN Order Pickup Service (01_source/order_pickup_service/app/main.py)",
    version=get_version(),
)


# Routers
app.include_router(orders.router)
app.include_router(kiosk.router)
app.include_router(pickup.router)
app.include_router(internal.router)

# Inclui os routers de healthcheck
app.include_router(health_router, tags=["Health"])
app.include_router(internal_router, tags=["Internal"])

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://taki.pt",
        "https://molrealestate.pt",
        "https://queroterreno.pt",
        "https://propertypartners.pt",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

expiry_task: asyncio.Task | None = None

@app.on_event("startup")
async def startup():
    # asyncio.create_task(expiry_loop())

    init_db()

    required_modules = ["app.schemas.kiosk"]
    for module in required_modules:
        try:
            init_database()
            __import__(module)
            logger.info("✅ Módulo %s carregado com sucesso", module)
        except ImportError as e:
            logger.exception("❌ Erro ao carregar %s: %s", module, e)
            raise  # não use sys.exit dentro do servidor -  Solução Correta: Usar raise

    global expiry_task
    if expiry_task is None:
        expiry_task = asyncio.create_task(expiry_loop(), name="expiry_loop")

@app.on_event("shutdown")
async def shutdown():
    global expiry_task
    if expiry_task:
        expiry_task.cancel()
        try:
            await expiry_task
        except asyncio.CancelledError:
            pass
        expiry_task = None


async def expiry_loop():
    while True:
        db = SessionLocal()
        try:
            # ✅ RODA EM THREAD (não bloqueia o event loop)
            await asyncio.to_thread(run_expiry_once, db)
        except Exception:
            logger.exception("expiry job failed")
        finally:
            db.close()

        await asyncio.sleep(EXPIRY_POLL_SEC)

# Transforme o 500 em JSON (handler global)
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "service": "order_pickup_service",
            "result": "error",
            "error": {"type": exc.__class__.__name__, "message": str(exc)},
            "severity": "HIGH",
            "severity_code": "GATEWAY_UNHANDLED_EXCEPTION",
            "timestamp": time.time(),
            # em prod você removeria stacktrace; em lab ajuda muito:
            "debug": {
                "path": str(request.url.path),
                "traceback": traceback.format_exc().splitlines()[-40:],
            },
        },
    )