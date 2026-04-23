# 01_source/backend/billing_fiscal_service/app/integrations/order_pickup_client.py
from __future__ import annotations

from typing import Any

import requests

from app.core.config import settings


class OrderPickupClientError(Exception):
    pass


def _internal_get(path: str) -> dict[str, Any]:
    url = f"{settings.order_pickup_service_url.rstrip('/')}{path}"
    headers = {
        "X-Internal-Token": settings.internal_token,
        "Accept": "application/json",
    }
    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=settings.order_pickup_timeout_sec,
        )
    except requests.RequestException as exc:
        raise OrderPickupClientError(f"Falha ao consultar order_pickup_service: {exc}") from exc

    if response.status_code >= 400:
        try:
            detail = response.json()
        except Exception:
            detail = response.text
        raise OrderPickupClientError(
            f"Consulta ao order_pickup_service falhou: status={response.status_code} detail={detail}"
        )

    try:
        return response.json()
    except Exception as exc:
        raise OrderPickupClientError("Resposta inválida do order_pickup_service.") from exc


def get_order_fiscal_context(order_id: str) -> dict[str, Any]:
    """Contrato v2 (O-1): order + items + locker_address + tenant fiscal + consumidor."""
    return _internal_get(f"/internal/orders/{order_id}/fiscal-context")


def get_order_invoice_source(order_id: str) -> dict[str, Any]:
    """I-1: mesma carga que fiscal-context; rota alternativa para retry após falha de transporte."""
    return _internal_get(f"/internal/orders/{order_id}/invoice-source")


def get_order_snapshot(order_id: str) -> dict[str, Any]:
    """Snapshot por /status — com full_fiscal=1 para alinhar ao contrato v2 no fallback."""
    return _internal_get(f"/internal/orders/{order_id}/status?full_fiscal=1")


def _is_not_found_error(exc: OrderPickupClientError) -> bool:
    s = str(exc).lower()
    return "404" in str(exc) or "not found" in s


def _is_recoverable_transport_error(exc: OrderPickupClientError) -> bool:
    if isinstance(exc.__cause__, requests.RequestException):
        return True
    s = str(exc).lower()
    for token in (
        "502",
        "503",
        "504",
        "timeout",
        "timed out",
        "connection refused",
        "connection aborted",
        "httpconnectionpool",
        "httpsconnectionpool",
        "max retries exceeded",
        "failed to establish",
    ):
        if token in s:
            return True
    return False


def _snapshot_from_fiscal_payload(payload: dict[str, Any]) -> dict[str, Any] | None:
    if not isinstance(payload, dict) or not payload.get("contract_version"):
        return None
    order = payload.get("order") or {}
    return {
        "order": order,
        "allocation": payload.get("allocation"),
        "pickup": payload.get("pickup"),
        "order_items": payload.get("order_items"),
        "locker_address": payload.get("locker_address"),
        "tenant_fiscal": payload.get("tenant_fiscal"),
        "tenant_cnpj": payload.get("tenant_cnpj"),
        "tenant_razao_social": payload.get("tenant_razao_social"),
        "consumer_cpf": payload.get("consumer_cpf"),
        "consumer_name": payload.get("consumer_name"),
        "locker_id": payload.get("locker_id"),
        "contract_version": payload.get("contract_version"),
    }


def _legacy_status_as_snapshot(raw: dict[str, Any]) -> dict[str, Any]:
    """Resposta /status sem contract_version (full_fiscal falhou ou legado)."""
    return {
        "order": raw.get("order") or {},
        "allocation": raw.get("allocation"),
        "pickup": raw.get("pickup"),
    }


def get_order_snapshot_for_invoice(order_id: str) -> dict[str, Any]:
    """
    Preferência: fiscal-context v2.
    I-1: em 404 (rota ou recurso) tenta /status com full_fiscal; em timeout/5xx tenta invoice-source
    e depois /status.
    """
    try:
        ctx = get_order_fiscal_context(order_id)
        mapped = _snapshot_from_fiscal_payload(ctx)
        if mapped is not None:
            return mapped
    except OrderPickupClientError as exc:
        if _is_not_found_error(exc):
            snap = get_order_snapshot(order_id)
            mapped = _snapshot_from_fiscal_payload(snap)
            return mapped if mapped is not None else _legacy_status_as_snapshot(snap)
        if _is_recoverable_transport_error(exc):
            try:
                ctx2 = get_order_invoice_source(order_id)
                mapped = _snapshot_from_fiscal_payload(ctx2)
                if mapped is not None:
                    return mapped
            except OrderPickupClientError:
                pass
            try:
                snap = get_order_snapshot(order_id)
                mapped = _snapshot_from_fiscal_payload(snap)
                return mapped if mapped is not None else _legacy_status_as_snapshot(snap)
            except OrderPickupClientError:
                pass
        raise

    snap = get_order_snapshot(order_id)
    mapped = _snapshot_from_fiscal_payload(snap)
    return mapped if mapped is not None else _legacy_status_as_snapshot(snap)
