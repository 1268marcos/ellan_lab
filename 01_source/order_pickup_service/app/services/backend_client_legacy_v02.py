# 01_source/order_pickup_service/app/services/backend_client.py
from typing import Optional
import requests
from app.core.config import settings


# =========================================================
# 🔥 NOVO PADRÃO: TUDO VIA RUNTIME (SEM REGION BACKEND)
# =========================================================

def _base() -> str:
    return settings.runtime_internal.rstrip("/")


def _normalize_locker_id(locker_id: Optional[str]) -> Optional[str]:
    normalized = str(locker_id or "").strip()
    return normalized or None


def _headers_for_locker(locker_id: Optional[str] = None) -> dict:
    headers = {
        "X-Internal-Token": settings.internal_token,
    }
    
    normalized = _normalize_locker_id(locker_id)
    if normalized:
        headers["X-Locker-Id"] = normalized
    
    return headers


# =========================================================
# LOCKER REGISTRY (gateway)
# =========================================================

def get_locker_registry_item(locker_id: str) -> Optional[dict]:
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


# =========================================================
# PRICING (RUNTIME)
# =========================================================

def get_sku_pricing(region: str, sku_id: str, locker_id: str | None = None) -> dict:
    normalized_sku_id = str(sku_id or "").strip()
    if not normalized_sku_id:
        raise ValueError("sku_id is required")
    
    base = _base()
    path = settings.backend_price_path_template.format(sku_id=normalized_sku_id)
    url = f"{base}{path}"
    
    r = requests.get(
        url,
        headers=_headers_for_locker(locker_id),
        timeout=settings.backend_client_timeout_sec,
    )
    
    r.raise_for_status()
    return r.json()


# =========================================================
# LOCKER ACTIONS (RUNTIME)
# =========================================================

def locker_allocate(
    region: str,
    sku_id: str,
    ttl_sec: int,
    request_id: str,
    desired_slot: int | None = None,
    locker_id: str | None = None,
) -> dict:
    
    if not locker_id:
        raise ValueError("locker_id is requerid for runtime allocate")

    base = _base()
    url = f"{base}/locker/allocate"
    
    payload = {
        "locker_id": locker_id, # CRÍTICO
        "sku_id": sku_id,
        "ttl_sec": int(ttl_sec),
        "request_id": request_id,
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
    
    base = _base()
    url = f"{base}/locker/allocations/{allocation_id}/commit"
    
    r = requests.post(
        url,
        json={"locker_id": locker_id, "locked_until": locked_until_iso},
        headers=_headers_for_locker(locker_id),
        timeout=settings.backend_client_timeout_sec,
    )
    
    r.raise_for_status()
    return r.json()


def locker_release(region: str, allocation_id: str, locker_id: str | None = None) -> dict:
    base = _base()
    url = f"{base}/locker/allocations/{allocation_id}/release"
    
    r = requests.post(
        url,
        json={"locker_id": locker_id},
        headers=_headers_for_locker(locker_id),
        timeout=settings.backend_client_timeout_sec,
    )
    
    r.raise_for_status()
    return r.json()


def locker_open(region: str, slot: int, locker_id: str | None = None) -> dict:
    base = _base()
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
    base = _base()
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
    
    base = _base()
    url = f"{base}/locker/slots/{int(slot)}/set-state"
    
    payload = {"state": state}
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