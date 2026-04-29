from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import text

from app.core.config import settings
from app.core.db import SessionLocal
from app.core.version import get_app_info

import logging
import time

logger = logging.getLogger("order_pickup_service")
router = APIRouter()


async def verify_internal_token(authorization: Optional[str] = Header(None)):
    """
    Verifica se o token interno é válido.
    O token deve ser passado no header Authorization: Bearer <token>
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Token não fornecido")

    try:
        token = authorization.split(" ")[1]
    except IndexError:
        raise HTTPException(status_code=401, detail="Formato de token inválido")

    if token != settings.internal_health_token:
        raise HTTPException(status_code=403, detail="Token inválido")

    return True


async def check_database() -> dict:
    """Verifica se o banco de dados está respondendo."""
    start_time = time.time()
    db = SessionLocal()

    try:
        result = db.execute(text("SELECT 1")).scalar()
        latency = round((time.time() - start_time) * 1000, 2)

        if result == 1:
            return {
                "status": "healthy",
                "message": "Conexão com banco de dados OK",
                "latency_ms": latency,
            }

        return {
            "status": "unhealthy",
            "message": "Banco de dados retornou resultado inesperado",
            "latency_ms": latency,
        }
    except Exception as exc:
        logger.error(
            "Erro na verificação do banco de dados",
            extra={"error_type": exc.__class__.__name__},
        )
        return {
            "status": "unhealthy",
            "message": "Erro no banco de dados.",
            "error_type": exc.__class__.__name__,
            "latency_ms": round((time.time() - start_time) * 1000, 2),
        }
    finally:
        db.close()


def check_expiry_job() -> dict:
    """Verifica se o job de expiry está rodando."""
    from app.main import expiry_task

    if expiry_task and not expiry_task.done():
        return {
            "status": "healthy",
            "message": "Expiry job está rodando",
            "task_name": expiry_task.get_name(),
        }

    return {
        "status": "warning",
        "message": "Expiry job não está rodando ou foi finalizado",
    }


@router.get("/internal/health")
async def internal_health_check(authorized: bool = Depends(verify_internal_token)):
    """
    Healthcheck interno - requer token de autenticação.
    Verifica conexão com banco de dados e outros serviços.
    """
    app_info = get_app_info()
    app_info["timestamp"] = datetime.now(timezone.utc)

    health_status = {
        **app_info,
        "checks": {},
    }

    db_status = await check_database()
    health_status["checks"]["database"] = db_status
    health_status["checks"]["expiry_job"] = check_expiry_job()

    if all(
        check["status"] in {"healthy", "warning"}
        for check in health_status["checks"].values()
    ):
        health_status["status"] = "healthy"
        return health_status

    health_status["status"] = "degraded"
    raise HTTPException(status_code=503, detail=health_status)


@router.get("/internal/health/ready")
async def readiness_check(authorized: bool = Depends(verify_internal_token)):
    """
    Readiness probe para Kubernetes.
    Indica se a aplicação está pronta para receber tráfego.
    """
    db_status = await check_database()

    if db_status["status"] == "healthy":
        return {
            "status": "ready",
            "message": "Aplicação pronta para receber tráfego",
            "timestamp": datetime.now(timezone.utc),
        }

    raise HTTPException(
        status_code=503,
        detail={
            "status": "not_ready",
            "message": "Aplicação não está pronta",
            "reason": db_status["message"],
        },
    )


@router.get("/internal/health/live")
async def liveness_check(authorized: bool = Depends(verify_internal_token)):
    """
    Liveness probe para Kubernetes.
    Indica se a aplicação está viva (não travada).
    """
    return {
        "status": "alive",
        "message": "Aplicação está rodando",
        "timestamp": datetime.now(timezone.utc),
    }


@router.get("/internal/health/detailed")
async def detailed_health_check(authorized: bool = Depends(verify_internal_token)):
    """
    Healthcheck detalhado com informações de sistema.
    Útil para debugging.
    """
    import platform
    import psutil

    system_info = {
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_usage": psutil.disk_usage("/").percent,
    }

    app_info = get_app_info()
    app_info["timestamp"] = datetime.now(timezone.utc)

    db_status = await check_database()

    return {
        **app_info,
        "status": "healthy" if db_status["status"] == "healthy" else "degraded",
        "checks": {
            "database": db_status,
            "expiry_job": check_expiry_job(),
        },
        "system": system_info,
    }