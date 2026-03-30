# 01_source/backend/runtime/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.health import router as health_router
from app.routers.internal_runtime import router as internal_runtime_router

app = FastAPI(
    title="ELLAN Backend Operacional Canônico - runtime operacional multi-locker",
    version="1.0.1",
)

app.include_router(health_router)
app.include_router(internal_runtime_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
