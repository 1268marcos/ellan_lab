import os
import requests

# Bases internas (container->container)
BACKEND_SP_INTERNAL = os.getenv("BACKEND_SP_INTERNAL", "http://backend_sp:8000")
BACKEND_PT_INTERNAL = os.getenv("BACKEND_PT_INTERNAL", "http://backend_pt:8000")

# Template do path de preço (já existe no seu compose)
BACKEND_PRICE_PATH_TEMPLATE = os.getenv("BACKEND_PRICE_PATH_TEMPLATE", "/catalog/skus/{sku_id}")

def _base(region: str) -> str:
    r = (region or "").upper()
    if r == "SP":
        return BACKEND_SP_INTERNAL
    if r == "PT":
        return BACKEND_PT_INTERNAL
    # fallback seguro
    return BACKEND_PT_INTERNAL

def get_sku_pricing(region: str, sku_id: str) -> dict:
    base = _base(region).rstrip("/")
    path = BACKEND_PRICE_PATH_TEMPLATE.format(sku_id=sku_id)
    url = f"{base}{path}"
    r = requests.get(url, timeout=5)
    r.raise_for_status()
    return r.json()

def locker_allocate(region: str, sku_id: str, ttl_sec: int, request_id: str) -> dict:
    base = _base(region).rstrip("/")
    url = f"{base}/locker/allocate"
    payload = {"sku_id": sku_id, "ttl_sec": int(ttl_sec), "request_id": request_id}
    r = requests.post(url, json=payload, timeout=5)
    r.raise_for_status()
    return r.json()

def locker_commit(region: str, allocation_id: str, locked_until: str | None = None) -> dict:
    base = _base(region).rstrip("/")
    url = f"{base}/locker/allocations/{allocation_id}/commit"
    payload = {"locked_until": locked_until}
    r = requests.post(url, json=payload, timeout=5)
    r.raise_for_status()
    return r.json()

def locker_release(region: str, allocation_id: str) -> dict:
    base = _base(region).rstrip("/")
    url = f"{base}/locker/allocations/{allocation_id}/release"
    r = requests.post(url, json={}, timeout=5)
    r.raise_for_status()
    return r.json()

def locker_open(region: str, slot: int) -> dict:
    base = _base(region).rstrip("/")
    url = f"{base}/locker/slots/{int(slot)}/open"
    r = requests.post(url, json={}, timeout=5)
    r.raise_for_status()
    return r.json()

def locker_light_on(region: str, slot: int) -> dict:
    base = _base(region).rstrip("/")
    url = f"{base}/locker/slots/{int(slot)}/light/on"
    r = requests.post(url, json={}, timeout=5)
    r.raise_for_status()
    return r.json()

def locker_set_state(region: str, slot: int, state: str, product_id: str | None = None) -> dict:
    base = _base(region).rstrip("/")
    url = f"{base}/locker/slots/{int(slot)}/set-state"
    payload = {"state": state, "product_id": product_id}
    r = requests.post(url, json=payload, timeout=5)
    r.raise_for_status()
    return r.json()

# 02-03-2026
def pickup_verify(region: str, order_id: str, step_index: int, expires_at: int, signature: str,
                  locker_id: str, porta: int, gateway_id: str):
    base = os.getenv("BACKEND_PT_EXTERNAL") if region == "PT" else os.getenv("BACKEND_SP_EXTERNAL")
    url = f"{base}/internal/pickup/verify"  # endpoint no backend (não no pickup_service)
    headers = {"X-Internal-Token": os.getenv("INTERNAL_TOKEN", "")}

    payload = {
        "order_id": order_id,
        "step_index": step_index,
        "expires_at": expires_at,
        "signature": signature,
        "locker_id": locker_id,
        "porta": porta,
        "gateway_id": gateway_id,
        "region": region,
    }

    r = requests.post(url, json=payload, headers=headers, timeout=DEFAULT_TIMEOUT)
    r.raise_for_status()
    return r.json()