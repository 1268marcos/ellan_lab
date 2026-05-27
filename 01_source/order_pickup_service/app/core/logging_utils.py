from __future__ import annotations

import functools
import inspect
from collections.abc import Callable
from typing import Any, TypeVar

from app.core.structured_logging import bind_log_context, get_logger

F = TypeVar("F", bound=Callable[..., Any])


def _resolve_order_id(
    *,
    bound_args: inspect.BoundArguments,
    order_id_param: str | None,
) -> str | None:
    if not order_id_param:
        return None
    if order_id_param in bound_args.arguments:
        value = bound_args.arguments[order_id_param]
        return str(value).strip() if value is not None else None
    return None


def bind_endpoint_context(
    *,
    operation: str,
    order_id_param: str | None = "order_id",
    critical: bool = True,
) -> Callable[[F], F]:
    """
    Decorator para endpoints críticos: enriquece logs com ``operation`` e ``order_id``.

    O middleware já define ``correlation_id``; este decorator adiciona contexto de negócio
    e registra início/sucesso/falha com stack trace em erros não tratados.
    """

    def decorator(func: F) -> F:
        logger = get_logger(func.__module__)
        is_async = inspect.iscoroutinefunction(func)

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            sig = inspect.signature(func)
            bound = sig.bind_partial(*args, **kwargs)
            bound.apply_defaults()
            order_id = _resolve_order_id(bound_args=bound, order_id_param=order_id_param)
            bind_log_context(
                operation=operation,
                order_id=order_id,
                critical_endpoint=critical,
            )
            logger.info(
                "endpoint_started",
                operation=operation,
                order_id=order_id,
                endpoint=func.__name__,
            )
            try:
                result = await func(*args, **kwargs)
                logger.info(
                    "endpoint_succeeded",
                    operation=operation,
                    order_id=order_id,
                    endpoint=func.__name__,
                )
                return result
            except Exception as exc:
                logger.exception(
                    "endpoint_failed",
                    operation=operation,
                    order_id=order_id,
                    endpoint=func.__name__,
                    error_type=exc.__class__.__name__,
                    error_message=str(exc)[:500],
                )
                raise

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            sig = inspect.signature(func)
            bound = sig.bind_partial(*args, **kwargs)
            bound.apply_defaults()
            order_id = _resolve_order_id(bound_args=bound, order_id_param=order_id_param)
            bind_log_context(
                operation=operation,
                order_id=order_id,
                critical_endpoint=critical,
            )
            logger.info(
                "endpoint_started",
                operation=operation,
                order_id=order_id,
                endpoint=func.__name__,
            )
            try:
                result = func(*args, **kwargs)
                logger.info(
                    "endpoint_succeeded",
                    operation=operation,
                    order_id=order_id,
                    endpoint=func.__name__,
                )
                return result
            except Exception as exc:
                logger.exception(
                    "endpoint_failed",
                    operation=operation,
                    order_id=order_id,
                    endpoint=func.__name__,
                    error_type=exc.__class__.__name__,
                    error_message=str(exc)[:500],
                )
                raise

        return async_wrapper if is_async else sync_wrapper  # type: ignore[return-value]

    return decorator
