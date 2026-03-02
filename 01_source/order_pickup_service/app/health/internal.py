# 01_source/order_pickup_service/app/health/internal.py
from app.schemas.internal import PickupVerifyIn, PickupVerifyOut, PickupConfirmIn, EventsBatchIn

from app.core.db import SessionLocal
from app.core.version import get_app_info
from app.database import SessionLocal
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import text
from typing import Optional, Dict, Any
import logging
import os
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
    
    # Extrai o token do header
    try:
        token = authorization.split(" ")[1]
    except IndexError:
        raise HTTPException(status_code=401, detail="Formato de token inválido")
    
    # Verifica o token - pega do ambiente ou usa um valor fixo
    expected_token = os.getenv("INTERNAL_HEALTH_TOKEN", "secret-token-123")
    
    if token != expected_token:
        raise HTTPException(status_code=403, detail="Token inválido")
    
    return True

@router.get("/internal/health")
async def internal_health_check(authorized: bool = Depends(verify_internal_token)):
    """
    Healthcheck interno - requer token de autenticação.
    Verifica conexão com banco de dados e outros serviços.
    """
    app_info = get_app_info()
    app_info["timestamp"] = datetime.utcnow().isoformat()
    
    health_status = {
        **app_info,
        "checks": {}
    }
    
    # Verifica conexão com banco de dados
    db_status = await check_database()
    health_status["checks"]["database"] = db_status
    
    # Verifica outros serviços (exemplo: Redis)
    # redis_status = await check_redis()
    # health_status["checks"]["redis"] = redis_status
    
    # Define status geral baseado nos checks
    if all(check["status"] == "healthy" for check in health_status["checks"].values()):
        health_status["status"] = "healthy"
        status_code = 200
    else:
        health_status["status"] = "degraded"
        status_code = 503
    
    return health_status


async def check_database() -> dict:
    """Verifica se o banco de dados está respondendo."""
    start_time = time.time()
    db = SessionLocal()
    
    try:
        # Executa query simples para testar conexão
        result = db.execute(text("SELECT 1")).scalar()
        latency = round((time.time() - start_time) * 1000, 2)
        
        if result == 1:
            return {
                "status": "healthy",
                "message": "Conexão com banco de dados OK",
                "latency_ms": latency
            }
        else:
            return {
                "status": "unhealthy",
                "message": "Banco de dados retornou resultado inesperado",
                "latency_ms": latency
            }
    except Exception as e:
        logger.error(f"Erro na verificação do banco de dados: {e}")
        return {
            "status": "unhealthy",
            "message": f"Erro no banco de dados: {str(e)}",
            "latency_ms": round((time.time() - start_time) * 1000, 2)
        }
    finally:
        db.close()

# Opcional: healthcheck mais detalhado para Kubernetes
@router.get("/internal/health/ready")
async def readiness_check(authorized: bool = Depends(verify_internal_token)):
    """
    Readiness probe para Kubernetes.
    Indica se a aplicação está pronta para receber tráfego.
    """
    # Verifica se todos os serviços necessários estão prontos
    db_status = await check_database()
    
    if db_status["status"] == "healthy":
        return {"status": "ready", "message": "Aplicação pronta"}
    else:
        raise HTTPException(status_code=503, detail="Aplicação não está pronta")

@router.get("/internal/health/live")
async def liveness_check(authorized: bool = Depends(verify_internal_token)):
    """
    Liveness probe para Kubernetes.
    Indica se a aplicação está viva (não travada).
    """
    return {"status": "alive", "message": "Aplicação está rodando"}


def check_expiry_job() -> dict:
    """Verifica se o job de expiry está rodando."""
    from app.main import expiry_task
    
    if expiry_task and not expiry_task.done():
        return {
            "status": "healthy",
            "message": "Expiry job está rodando",
            "task_name": expiry_task.get_name()
        }
    else:
        return {
            "status": "warning",
            "message": "Expiry job não está rodando ou foi finalizado"
        }



# Healthcheck detalhado para Kubernetes
@router.get("/internal/health/ready")
async def readiness_check(authorized: bool = Depends(verify_internal_token)):
    """
    Readiness probe para Kubernetes.
    Indica se a aplicação está pronta para receber tráfego.
    """
    # Verifica se todos os serviços necessários estão prontos
    db_status = await check_database()
    
    if db_status["status"] == "healthy":
        return {
            "status": "ready",
            "message": "Aplicação pronta para receber tráfego",
            "timestamp": datetime.utcnow().isoformat()
        }
    else:
        raise HTTPException(
            status_code=503, 
            detail={
                "status": "not_ready",
                "message": "Aplicação não está pronta",
                "reason": db_status["message"]
            }
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
        "timestamp": datetime.utcnow().isoformat()
    }

# Endpoint para diagnóstico mais detalhado
@router.get("/internal/health/detailed")
async def detailed_health_check(authorized: bool = Depends(verify_internal_token)):
    """
    Healthcheck detalhado com informações de sistema.
    Útil para debugging.
    """
    import psutil
    import platform
    
    # Informações do sistema
    system_info = {
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_usage": psutil.disk_usage('/').percent
    }
    
    # Healthcheck básico
    basic_health = await internal_health_check(authorized)
    
    return {
        **basic_health,
        "system": system_info
    }


