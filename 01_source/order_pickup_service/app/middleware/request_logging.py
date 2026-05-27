from __future__ import annotations

import re
import time
import uuid
from collections import defaultdict, deque
from typing import Callable

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.config import settings
from app.core.structured_logging import bind_log_context, clear_log_context, get_logger

logger = get_logger("request_logging")

# Prefixos de rotas críticas (pagamento, pedido, pickup, reconciliação, etc.)
CRITICAL_PATH_PREFIXES: tuple[str, ...] = (
    "/public/orders",
    "/public/pickup",
    "/public/me",
    "/public/auth",
    "/public/fiscal",
    "/orders",
    "/v1/orders",
    "/totem/pickups",
    "/pickup",
    "/kiosk",
    "/payment-capabilities",
    "/internal/",
    "/dev-admin",
    "/ops/",
    "/partners/",
    "/runtime-sync",
    "/locker",
)

_ORDER_ID_SKIP_SEGMENTS = frozenset(
    {
        "",
        "cancel",
        "invoice-pdf",
        "invoice-resend-email",
        "invoice-generate",
        "fulfillment",
        "partner-events",
        "partner-lookup",
    }
)

_ORDER_ID_PATH_RE = re.compile(
    r"/(?:public/)?orders/(?P<order_id>[^/]+)",
    re.IGNORECASE,
)


def resolve_correlation_id(request: Request) -> str:
    header = (
        request.headers.get("X-Correlation-Id")
        or request.headers.get("X-Correlation-ID")
        or request.headers.get("X-Trace-Id")
        or request.headers.get("X-Trace-ID")
    )
    return str(header).strip() if header else str(uuid.uuid4())


def is_critical_path(path: str) -> bool:
    normalized = str(path or "").lower()
    return any(normalized.startswith(prefix.lower()) for prefix in CRITICAL_PATH_PREFIXES)


def extract_order_id_from_path(path: str) -> str | None:
    match = _ORDER_ID_PATH_RE.search(str(path or ""))
    if not match:
        return None
    candidate = str(match.group("order_id") or "").strip()
    if not candidate or candidate.lower() in _ORDER_ID_SKIP_SEGMENTS:
        return None
    return candidate


class _PublicRouteRateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max(1, int(max_requests))
        self.window_seconds = max(1, int(window_seconds))
        self._events: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str, now_ts: float) -> bool:
        events = self._events[key]
        window_start = now_ts - self.window_seconds
        while events and events[0] < window_start:
            events.popleft()
        if len(events) >= self.max_requests:
            return False
        events.append(now_ts)
        return True


_public_rate_limiter = _PublicRouteRateLimiter(
    max_requests=settings.public_rate_limit_requests,
    window_seconds=settings.public_rate_limit_window_sec,
)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Por request:
    - correlation_id (UUID ou header)
    - contexto structlog (method, path, order_id, critical)
    - duração em ms
    - stack trace completo em exceções não tratadas
    """

    def __init__(
        self,
        app,
        *,
        record_dev_error_event: Callable[..., None] | None = None,
    ):
        super().__init__(app)
        self._record_dev_error_event = record_dev_error_event

    async def dispatch(self, request: Request, call_next) -> Response:
        clear_log_context()
        correlation_id = resolve_correlation_id(request)
        request.state.correlation_id = correlation_id
        request.state.trace_id = correlation_id  # compatível com código existente

        path = str(request.url.path or "")
        order_id = extract_order_id_from_path(path)
        critical = is_critical_path(path)

        bind_log_context(
            correlation_id=correlation_id,
            order_id=order_id,
            http_method=request.method,
            http_path=path,
            critical_endpoint=critical,
        )

        started = time.perf_counter()

        if path.startswith("/public/"):
            client_ip = request.client.host if request.client else "unknown"
            rate_key = f"{client_ip}:{path}"
            if not _public_rate_limiter.allow(rate_key, time.time()):
                duration_ms = int((time.perf_counter() - started) * 1000)
                logger.warning(
                    "request_rate_limited",
                    duration_ms=duration_ms,
                    status_code=429,
                )
                return JSONResponse(
                    status_code=429,
                    content={
                        "service": "order_pickup_service",
                        "result": "error",
                        "error": {"type": "RATE_LIMIT_EXCEEDED", "message": "Too many requests"},
                        "correlation_id": correlation_id,
                        "trace_id": correlation_id,
                    },
                    headers={
                        "X-Correlation-Id": correlation_id,
                        "X-Trace-Id": correlation_id,
                    },
                )

        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = int((time.perf_counter() - started) * 1000)
            logger.exception(
                "request_failed_unhandled",
                duration_ms=duration_ms,
                error_type=exc.__class__.__name__,
                error_message=str(exc)[:500],
            )
            if self._record_dev_error_event:
                self._record_dev_error_event(
                    level="UNHANDLED_EXCEPTION",
                    status_code=500,
                    path=path,
                    method=request.method,
                    trace_id=correlation_id,
                    error_type=exc.__class__.__name__,
                    message=str(exc)[:300],
                )
            raise
        else:
            duration_ms = int((time.perf_counter() - started) * 1000)
            status_code = int(response.status_code)
            log_fn = logger.warning if status_code >= 400 else logger.info
            log_fn(
                "request_completed",
                duration_ms=duration_ms,
                status_code=status_code,
                critical_endpoint=critical,
                order_id=order_id,
            )

            if status_code >= 400 and self._record_dev_error_event:
                self._record_dev_error_event(
                    level="HTTP_ERROR",
                    status_code=status_code,
                    path=path,
                    method=request.method,
                    trace_id=correlation_id,
                )

            response.headers["X-Correlation-Id"] = correlation_id
            response.headers["X-Trace-Id"] = correlation_id
            return response
        finally:
            clear_log_context()
