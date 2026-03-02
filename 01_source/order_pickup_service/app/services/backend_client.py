# Cliente do backend SP/PT (preço + locker)
import os
import requests
from typing import Dict, Any

BACKEND_SP_BASE = os.getenv("BACKEND_SP_BASE", "http://localhost:8201")
BACKEND_PT_BASE = os.getenv("BACKEND_PT_BASE", "http://localhost:8202")

PRICE_PATH_TEMPLATE = os.getenv("BACKEND_PRICE_PATH_TEMPLATE", "/catalog/skus/{sku_id}")

DEFAULT_TIMEOUT = (2.0, 3.0)  # connect timeout, read timeout

def _base(region: str) -> str:
    if region == "SP":
        return BACKEND_SP_BASE
    if region == "PT":
        return BACKEND_PT_BASE
    raise ValueError("region must be SP or PT")

def get_sku_pricing(region: str, sku_id: str) -> Dict[str, Any]:
    """
    IMPORTANT: este endpoint você vai confirmar no backend.
    Esperado retornar pelo menos:
      - amount_cents (int) ou price_cents
      - currency (opcional)
    """
    url = _base(region) + PRICE_PATH_TEMPLATE.format(sku_id=sku_id)
    r = requests.get(url, timeout=5)
    r.raise_for_status()
    return r.json()

# Locker endpoints (já confirmados como existentes)
def locker_allocate(region: str, sku_id: str, ttl_sec: int, request_id: str) -> Dict[str, Any]:
    url = _base(region) + "/locker/allocate"
    payload = {"sku_id": sku_id, "ttl_sec": ttl_sec, "request_id": request_id}
    r = requests.post(url, json=payload, timeout=5)
    r.raise_for_status()
    return r.json()

def locker_commit(region: str, allocation_id: str, locked_until_iso: str | None) -> Dict[str, Any]:
    url = _base(region) + f"/locker/allocations/{allocation_id}/commit"
    payload = {"locked_until": locked_until_iso}
    r = requests.post(url, json=payload, timeout=5)
    r.raise_for_status()
    return r.json()

def locker_release(region: str, allocation_id: str) -> Dict[str, Any]:
    url = _base(region) + f"/locker/allocations/{allocation_id}/release"
    r = requests.post(url, json={}, timeout=5)
    r.raise_for_status()
    return r.json()

def locker_open(region: str, slot: int) -> Dict[str, Any]:
    url = _base(region) + f"/locker/slots/{slot}/open"
    r = requests.post(url, json={}, timeout=5)
    r.raise_for_status()
    return r.json()

def locker_light_on(region: str, slot: int) -> Dict[str, Any]:
    url = _base(region) + f"/locker/slots/{slot}/light/on"
    r = requests.post(url, json={}, timeout=5)
    r.raise_for_status()
    return r.json()

# PROPOSTO (pra “cinza / aguardar reposição”):
def locker_mark_out_of_stock(region: str, slot: int) -> Dict[str, Any]:
    url = _base(region) + f"/locker/slots/{slot}/mark-out-of-stock"
    r = requests.post(url, json={}, timeout=5)
    r.raise_for_status()
    return r.json()

def locker_set_state(region: str, slot: int, state: str) -> Dict[str, Any]:
    """
    Chama o backend do totem (SP/PT) para setar estado da gaveta.
    Ex.: state = "OUT_OF_STOCK"
    """
    url = _base(region) + f"/locker/slots/{slot}/set-state"
    r = requests.post(url, json={"state": state}, timeout=5)
    r.raise_for_status()
    return r.json()

# 02-03-2026
def pickup_verify(region: str, order_id: str, step_index: int, expires_at: int, signature: str,
                  locker_id: str, porta: int, gateway_id: str):
    base = os.getenv("BACKEND_PT_BASE") if region == "PT" else os.getenv("BACKEND_SP_BASE")
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