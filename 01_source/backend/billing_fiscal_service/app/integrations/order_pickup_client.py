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


def get_order_snapshot(order_id: str) -> dict[str, Any]:
    """Snapshot legado por /status — mantido para compatibilidade."""
    return _internal_get(f"/internal/orders/{order_id}/status")


def get_order_snapshot_for_invoice(order_id: str) -> dict[str, Any]:
    """
    Preferência: fiscal-context v2. Fallback para /status se rota ainda não existir (404).
    """
    try:
        ctx = get_order_fiscal_context(order_id)
    except OrderPickupClientError as exc:
        if "404" in str(exc) or "not found" in str(exc).lower():
            return get_order_snapshot(order_id)
        raise
    if isinstance(ctx, dict) and ctx.get("contract_version"):
        order = ctx.get("order") or {}
        return {
            "order": order,
            "allocation": ctx.get("allocation"),
            "pickup": ctx.get("pickup"),
            "order_items": ctx.get("order_items"),
            "locker_address": ctx.get("locker_address"),
            "tenant_fiscal": ctx.get("tenant_fiscal"),
            "tenant_cnpj": ctx.get("tenant_cnpj"),
            "tenant_razao_social": ctx.get("tenant_razao_social"),
            "consumer_cpf": ctx.get("consumer_cpf"),
            "consumer_name": ctx.get("consumer_name"),
            "locker_id": ctx.get("locker_id"),
            "contract_version": ctx.get("contract_version"),
        }
    return get_order_snapshot(order_id)
