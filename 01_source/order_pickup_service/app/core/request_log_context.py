from __future__ import annotations

from typing import Any

from fastapi import Request

from app.core.structured_logging import bind_log_context


def bind_request_log_context(request: Request, **extra: Any) -> None:
    """
    Uso manual em endpoints críticos (quando o decorator não cobre o caso).

    Exemplo::

        logger.info(
            "payment_confirmed",
            extra={
                "correlation_id": request.state.correlation_id,
                "order_id": order.id,
            },
        )
        bind_request_log_context(request, order_id=order.id)
        logger.info("payment_confirmed", order_id=order.id)
    """
    correlation_id = getattr(request.state, "correlation_id", None) or getattr(
        request.state, "trace_id", None
    )
    bind_log_context(
        correlation_id=correlation_id,
        **extra,
    )
