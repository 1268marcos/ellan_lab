# 01_source/order_pickup_service/app/services/backend_client.py
# 08/04/2026 - EM def locker_set_state INCLUIDO NOVOS EM payload

from __future__ import annotations

from typing import Optional

import requests

from app.core.config import settings


def _runtime_base() -> str:
    return settings.runtime_internal.rstrip("/")


def _gateway_base() -> str:
    return settings.payment_gateway_internal.rstrip("/")


def _normalize_locker_id(locker_id: Optional[str]) -> Optional[str]:
    normalized = str(locker_id or "").strip().upper()
    return normalized or None


def _headers_for_internal_request(locker_id: Optional[str] = None) -> dict:
    headers = {
        "X-Internal-Token": settings.internal_token,
    }

    normalized = _normalize_locker_id(locker_id)
    if normalized:
        headers["X-Locker-Id"] = normalized

    return headers


def get_locker_registry_item(locker_id: str) -> Optional[dict]:
    normalized = _normalize_locker_id(locker_id)
    if not normalized:
        return None

    path = settings.payment_gateway_lockers_path_template.format(locker_id=normalized)
    url = f"{_gateway_base()}{path}"

    response = requests.get(
        url,
        timeout=settings.backend_client_timeout_sec,
    )

    if response.status_code == 404:
        return None

    # response.raise_for_status()
    if not response.ok:
        try:
            error_body = response.json()
        except Exception:
            error_body = response.text

        raise Exception({
            "error": "runtime_failed_get_locker_registry_item",
            "status_code": response.status_code,
            "body": error_body
        })

    return response.json()


def get_sku_pricing(region: str, sku_id: str, locker_id: str | None = None) -> dict:
    normalized_sku_id = str(sku_id or "").strip()
    if not normalized_sku_id:
        raise ValueError("sku_id is required")

    path = settings.backend_price_path_template.format(sku_id=normalized_sku_id)
    url = f"{_runtime_base()}{path}"

    response = requests.get(
        url,
        headers=_headers_for_internal_request(locker_id),
        timeout=settings.backend_client_timeout_sec,
    )
    # response.raise_for_status()
    if not response.ok:
        try:
            error_body = response.json()
        except Exception:
            error_body = response.text

        raise Exception({
            "error": "runtime_failed_get_sku_pricing",
            "status_code": response.status_code,
            "body": error_body
        })

    return response.json()


def locker_allocate(
    region: str,
    sku_id: str,
    ttl_sec: int,
    request_id: str,
    desired_slot: int | None = None,
    locker_id: str | None = None,
) -> dict:
    normalized_locker_id = _normalize_locker_id(locker_id)
    if not normalized_locker_id:
        raise ValueError("locker_id is required for runtime allocate")

    if desired_slot is None:
        slot = None
    else:
        slot = int(desired_slot)
    
    allocation_id = f"al_{request_id.replace('-', '')}"

    url = f"{_runtime_base()}/locker/allocate"

    payload = {
        # "slot": slot,
        "allocation_id": allocation_id,
        "ttl_seconds": ttl_sec,
        "request_id": request_id,
    }
    
    if slot is not None:
        payload["slot"] = slot

    response = requests.post(
        url,
        json=payload,
        headers=_headers_for_internal_request(normalized_locker_id),
        timeout=settings.backend_client_timeout_sec,
    )
    # response.raise_for_status()
    if not response.ok:
        try:
            error_body = response.json()
        except Exception:
            error_body = response.text

        raise Exception({
            "error": "runtime_failed_locker_allocate",
            "status_code": response.status_code,
            "body": error_body
        })

    return response.json()


def locker_commit(
    region: str,
    allocation_id: str,
    locked_until_iso: str | None = None,
    locker_id: str | None = None,
) -> dict:
    normalized_locker_id = _normalize_locker_id(locker_id)
    if not normalized_locker_id:
        raise ValueError("locker_id is required for runtime commit")

    normalized_allocation_id = str(allocation_id or "").strip()
    if not normalized_allocation_id:
        raise ValueError("allocation_id is required for runtime commit")

    url = f"{_runtime_base()}/locker/allocations/{normalized_allocation_id}/commit"

    response = requests.post(
        url,
        json={},
        headers=_headers_for_internal_request(normalized_locker_id),
        timeout=settings.backend_client_timeout_sec,
    )
    # response.raise_for_status()
    if not response.ok:
        try:
            error_body = response.json()
        except Exception:
            error_body = response.text

        raise Exception({
            "error": "runtime_failed_locker_commit",
            "status_code": response.status_code,
            "body": error_body
        })
    
    return response.json()


def locker_release(
    region: str,
    allocation_id: str,
    locker_id: str | None = None,
) -> dict:
    normalized_locker_id = _normalize_locker_id(locker_id)
    if not normalized_locker_id:
        raise ValueError("locker_id is required for runtime release")

    normalized_allocation_id = str(allocation_id or "").strip()
    if not normalized_allocation_id:
        raise ValueError("allocation_id is required for runtime release")

    url = f"{_runtime_base()}/locker/allocations/{normalized_allocation_id}/release"

    response = requests.post(
        url,
        json={},
        headers=_headers_for_internal_request(normalized_locker_id),
        timeout=settings.backend_client_timeout_sec,
    )
    # response.raise_for_status()
    if not response.ok:
        try:
            error_body = response.json()
        except Exception:
            error_body = response.text

        raise Exception({
            "error": "runtime_failed_locker_release",
            "status_code": response.status_code,
            "body": error_body
        })

    return response.json()


def locker_open(region: str, slot: int, locker_id: str | None = None) -> dict:
    normalized_locker_id = _normalize_locker_id(locker_id)
    if not normalized_locker_id:
        raise ValueError("locker_id is required for runtime open")

    url = f"{_runtime_base()}/locker/slots/{int(slot)}/open"

    response = requests.post(
        url,
        json={},
        headers=_headers_for_internal_request(normalized_locker_id),
        timeout=settings.backend_client_timeout_sec,
    )
    # response.raise_for_status()
    if not response.ok:
        try:
            error_body = response.json()
        except Exception:
            error_body = response.text

        raise Exception({
            "error": "runtime_failed_locker_open",
            "status_code": response.status_code,
            "body": error_body
        })

    return response.json()


def locker_light_on(region: str, slot: int, locker_id: str | None = None) -> dict:
    normalized_locker_id = _normalize_locker_id(locker_id)
    if not normalized_locker_id:
        raise ValueError("locker_id is required for runtime light on")

    url = f"{_runtime_base()}/locker/slots/{int(slot)}/light/on"

    response = requests.post(
        url,
        json={},
        headers=_headers_for_internal_request(normalized_locker_id),
        timeout=settings.backend_client_timeout_sec,
    )
    # response.raise_for_status()
    if not response.ok:
        try:
            error_body = response.json()
        except Exception:
            error_body = response.text

        raise Exception({
            "error": "runtime_failed_locker_light_on",
            "status_code": response.status_code,
            "body": error_body
        })

    return response.json()


def locker_set_state(
    region: str,
    slot: int,
    state: str,
    product_id: str | None = None,
    locker_id: str | None = None,
) -> dict:
    normalized_locker_id = _normalize_locker_id(locker_id)
    if not normalized_locker_id:
        raise ValueError("locker_id is required for runtime set-state")

    normalized_state = str(state or "").strip().upper()
    if not normalized_state:
        raise ValueError("state is required for runtime set-state")

    url = f"{_runtime_base()}/locker/slots/{int(slot)}/set-state"

    payload = {
        "region": region,
        "totem_id": locker_id,
        "slot": slot,
        "state": normalized_state,
    }
    if product_id is not None:
        payload["product_id"] = product_id

    response = requests.post(
        url,
        json=payload,
        headers=_headers_for_internal_request(normalized_locker_id),
        timeout=settings.backend_client_timeout_sec,
    )
    # response.raise_for_status()
    if not response.ok:
        try:
            error_body = response.json()
        except Exception:
            error_body = response.text

        raise Exception({
            "error": "runtime_failed_locker_set_state",
            "status_code": response.status_code,
            "body": error_body
        })

    return response.json()


def get_allocation_state(
    allocation_id: str,
    locker_id: str | None = None,
) -> str:
    normalized_locker_id = _normalize_locker_id(locker_id)
    if not normalized_locker_id:
        raise ValueError("locker_id is required for allocation state")

    normalized_allocation_id = str(allocation_id or "").strip()
    if not normalized_allocation_id:
        raise ValueError("allocation_id is required")

    url = f"{_runtime_base()}/locker/allocations/{normalized_allocation_id}"

    response = requests.get(
        url,
        headers=_headers_for_internal_request(normalized_locker_id),
        timeout=settings.backend_client_timeout_sec,
    )

    if response.status_code == 404:
        return "NOT_FOUND"

    if not response.ok:
        try:
            error_body = response.json()
        except Exception:
            error_body = response.text

        raise Exception({
            "error": "runtime_failed_get_allocation_state",
            "status_code": response.status_code,
            "body": error_body
        })

    data = response.json()

    return data.get("state")


def get_slot_state(
    locker_id: str,
    slot: int,
) -> str:
    """
    Retorna o estado atual de uma gaveta (slot) no runtime.
    Fonte da verdade operacional.
    """
    normalized_locker_id = _normalize_locker_id(locker_id)
    if not normalized_locker_id:
        raise ValueError("locker_id is required for slot state")

    url = f"{_runtime_base()}/locker/slots"

    response = requests.get(
        url,
        headers=_headers_for_internal_request(normalized_locker_id),
        timeout=settings.backend_client_timeout_sec,
    )

    if not response.ok:
        try:
            error_body = response.json()
        except Exception:
            error_body = response.text

        raise Exception({
            "error": "runtime_failed_get_slots",
            "status_code": response.status_code,
            "body": error_body
        })

    slots = response.json()

    for s in slots:
        if int(s.get("slot")) == int(slot):
            return s.get("state")

    return "NOT_FOUND"
