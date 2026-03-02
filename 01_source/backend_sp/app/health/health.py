from fastapi import APIRouter, Response
from datetime import datetime
from app.core.version import get_app_info
import logging

logger = logging.getLogger("backend_sp")
router = APIRouter()

@router.get("/health")
async def health_check():
    """
    Healthcheck público - retorna status básico da aplicação.
    Não requer autenticação.
    Útil para load balancers e verificações externas.
    """
    try:
        app_info = get_app_info()
        app_info["timestamp"] = datetime.utcnow().isoformat()
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