from fastapi import APIRouter
from datetime import datetime, timezone
import logging

logger = logging.getLogger("order_pickup_service")
router = APIRouter()

@router.get("/health")
async def health_check():
    """Health check simples"""
    logger.info("Health check acessado")
    return {
        "status": "healthy",
        "service": "order_pickup_service",
        "timestamp": datetime.now(timezone.utc)
    }

@router.get("/health/ready")
async def ready_check():
    """Ready check"""
    return {"status": "ready"}

@router.get("/health/live")
async def live_check():
    """Live check"""
    return {"status": "alive"}




"""
from fastapi import APIRouter, Response
from datetime import datetime
from app.core.version import get_app_info
import logging

logger = logging.getLogger("order_pickup_service")
router = APIRouter()

@router.get("/health")
async def health_check():
    try:
        app_info = get_app_info()
        app_info["timestamp"] = datetime.now(timezone.utc)
        app_info["status"] = "healthy"
        
        logger.debug("Healthcheck público acessado")
        
        return Response(
            content=app_info,
            status_code=200,
            media_type="application/json"
        )
    except Exception as e:
        logger.error(f"Erro no healthcheck público: {e}")
        return Response(
            content={"status": "unhealthy", "error": str(e)},
            status_code=500,
            media_type="application/json"
        )
"""