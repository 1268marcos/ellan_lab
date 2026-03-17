# 01_source/order_pickup_service/app/services/backend_client.py
from typing import Optional

import requests

from app.core.config import settings


def _normalize_region(region: str) -> str:
    r = (region or "").upper().strip()
    if r not in {"SP", "PT"}:
        raise ValueError(f"unsupported region: {region}")
    return r


def _base(region: str) -> str:
    r = _normalize_region(region)
    if r == "SP":
        return settings.backend_sp_internal
    return settings.backend_pt_internal


def _normalize_locker_id(locker_id: Optional[str]) -> Optional[str]:
    normalized = str(locker_id or "").strip()
    return normalized or None


def _headers_for_locker(locker_id: Optional[str] = None) -> dict:
    headers = {}
    normalized = _normalize_locker_id(locker_id)
    if normalized:
        headers["X-Locker-Id"] = normalized
    return headers


def get_locker_registry_item(locker_id: str) -> Optional[dict]:
    """
    Consulta o registry central de lockers no payment_gateway.
    Retorna None se o locker não existir.
    """
    normalized = _normalize_locker_id(locker_id)
    if not normalized:
        return None

    base = settings.payment_gateway_internal.rstrip("/")
    path = settings.payment_gateway_lockers_path_template.format(locker_id=normalized)
    url = f"{base}{path}"

    r = requests.get(url, timeout=settings.backend_client_timeout_sec)

    if r.status_code == 404:
        return None

    r.raise_for_status()
    return r.json()


def get_sku_pricing(region: str, sku_id: str, locker_id: str | None = None) -> dict:
    normalized_sku_id = str(sku_id or "").strip()
    if not normalized_sku_id:
        raise ValueError("sku_id is required")

    base = _base(region).rstrip("/")
    path = settings.backend_price_path_template.format(sku_id=normalized_sku_id)
    url = f"{base}{path}"

    try:
        r = requests.get(
            url,
            headers=_headers_for_locker(locker_id),
            timeout=settings.backend_client_timeout_sec,
        )
        r.raise_for_status()
        return r.json()
    except requests.HTTPError as e:
        status = getattr(e.response, "status_code", None)
        if status == 404 and settings.dev_allow_unknown_sku:
            return {
                "sku_id": normalized_sku_id,
                "amount_cents": settings.dev_default_price_cents,
                "currency": settings.dev_default_currency,
                "source": "DEV_FALLBACK",
                "note": "SKU não encontrado no catálogo; usando preço default em DEV.",
            }
        raise


def locker_allocate(
    region: str,
    sku_id: str,
    ttl_sec: int,
    request_id: str,
    desired_slot: int | None = None,
    locker_id: str | None = None,
) -> dict:
    normalized_sku_id = str(sku_id or "").strip()
    normalized_request_id = str(request_id or "").strip()

    if not normalized_sku_id:
        raise ValueError("sku_id is required")
    if not normalized_request_id:
        raise ValueError("request_id is required")

    base = _base(region).rstrip("/")
    url = f"{base}/locker/allocate"

    payload = {
        "sku_id": normalized_sku_id,
        "ttl_sec": int(ttl_sec),
        "request_id": normalized_request_id,
    }
    if desired_slot is not None:
        payload["desired_slot"] = int(desired_slot)

    r = requests.post(
        url,
        json=payload,
        headers=_headers_for_locker(locker_id),
        timeout=settings.backend_client_timeout_sec,
    )
    r.raise_for_status()
    return r.json()


def locker_commit(
    region: str,
    allocation_id: str,
    locked_until_iso: str | None = None,
    locker_id: str | None = None,
) -> dict:
    normalized_allocation_id = str(allocation_id or "").strip()
    if not normalized_allocation_id:
        raise ValueError("allocation_id is required")

    base = _base(region).rstrip("/")
    url = f"{base}/locker/allocations/{normalized_allocation_id}/commit"
    payload = {"locked_until": locked_until_iso}

    r = requests.post(
        url,
        json=payload,
        headers=_headers_for_locker(locker_id),
        timeout=settings.backend_client_timeout_sec,
    )
    r.raise_for_status()
    return r.json()


def locker_release(region: str, allocation_id: str, locker_id: str | None = None) -> dict:
    normalized_allocation_id = str(allocation_id or "").strip()
    if not normalized_allocation_id:
        raise ValueError("allocation_id is required")

    base = _base(region).rstrip("/")
    url = f"{base}/locker/allocations/{normalized_allocation_id}/release"

    r = requests.post(
        url,
        json={},
        headers=_headers_for_locker(locker_id),
        timeout=settings.backend_client_timeout_sec,
    )
    r.raise_for_status()
    return r.json()


def locker_open(region: str, slot: int, locker_id: str | None = None) -> dict:
    base = _base(region).rstrip("/")
    url = f"{base}/locker/slots/{int(slot)}/open"

    r = requests.post(
        url,
        json={},
        headers=_headers_for_locker(locker_id),
        timeout=settings.backend_client_timeout_sec,
    )
    r.raise_for_status()
    return r.json()


def locker_light_on(region: str, slot: int, locker_id: str | None = None) -> dict:
    base = _base(region).rstrip("/")
    url = f"{base}/locker/slots/{int(slot)}/light/on"

    r = requests.post(
        url,
        json={},
        headers=_headers_for_locker(locker_id),
        timeout=settings.backend_client_timeout_sec,
    )
    r.raise_for_status()
    return r.json()


def locker_set_state(
    region: str,
    slot: int,
    state: str,
    product_id: str | None = None,
    locker_id: str | None = None,
) -> dict:
    normalized_state = str(state or "").strip()
    if not normalized_state:
        raise ValueError("state is required")

    base = _base(region).rstrip("/")
    url = f"{base}/locker/slots/{int(slot)}/set-state"

    payload = {"state": normalized_state}
    if product_id is not None:
        payload["product_id"] = product_id

    r = requests.post(
        url,
        json=payload,
        headers=_headers_for_locker(locker_id),
        timeout=settings.backend_client_timeout_sec,
    )
    r.raise_for_status()
    return r.json()