from __future__ import annotations

import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.config import feature_flags
from app.services import rollback_service

logger = logging.getLogger(__name__)


class ShadowModeMiddleware(BaseHTTPMiddleware):
    """Métricas HTTP + rollback automático; shadow compare é disparado em `v1_order_bridge`."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        try:
            feature_flags.record_http_outcome(status_code=int(response.status_code))
            rollback_service.observe_request_outcome(is_error=int(response.status_code) >= 400)
            if rollback_service.should_trigger_rollback():
                rollback_service.maybe_execute_rollback()
        except Exception:
            logger.exception("shadow_mode_middleware_post_dispatch_failed")
        return response
