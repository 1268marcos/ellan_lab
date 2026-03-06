import os
import requests

BACKEND_SP_INTERNAL = os.getenv("BACKEND_SP_INTERNAL", "http://backend_sp:8000")
BACKEND_PT_INTERNAL = os.getenv("BACKEND_PT_INTERNAL", "http://backend_pt:8000")
BACKEND_PRICE_PATH_TEMPLATE = os.getenv("BACKEND_PRICE_PATH_TEMPLATE", "/catalog/skus/{sku_id}")

DEV_ALLOW_UNKNOWN_SKU = os.getenv("DEV_ALLOW_UNKNOWN_SKU", "false").lower() == "true"
DEV_DEFAULT_PRICE_CENTS = int(os.getenv("DEV_DEFAULT_PRICE_CENTS", "1000"))  # 10.00 em cents
DEV_DEFAULT_CURRENCY = os.getenv("DEV_DEFAULT_CURRENCY", "EUR")


def _base(region: str) -> str:
    r = (region or "").upper()
    if r == "SP":
        return BACKEND_SP_INTERNAL
    if r == "PT":
        return BACKEND_PT_INTERNAL
    return BACKEND_PT_INTERNAL


def get_sku_pricing(region: str, sku_id: str) -> dict:
    base = _base(region).rstrip("/")
    path = BACKEND_PRICE_PATH_TEMPLATE.format(sku_id=sku_id)
    url = f"{base}{path}"

    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        return r.json()
    except requests.HTTPError as e:
        status = getattr(e.response, "status_code", None)
        # Fallback DEV: deixa o resto do sistema evoluir sem catálogo pronto
        if status == 404 and DEV_ALLOW_UNKNOWN_SKU:
            return {
                "sku_id": sku_id,
                "amount_cents": DEV_DEFAULT_PRICE_CENTS,
                "currency": DEV_DEFAULT_CURRENCY,
                "source": "DEV_FALLBACK",
                "note": "SKU não encontrado no catálogo; usando preço default em DEV.",
            }
        raise

def locker_allocate(region: str, sku_id: str, ttl_sec: int, request_id: str, desired_slot: int | None = None) -> dict:
    base = _base(region).rstrip("/")
    url = f"{base}/locker/allocate"
    payload = {
        "sku_id": sku_id,
        "ttl_sec": int(ttl_sec),
        "request_id": request_id,
    }
    if desired_slot is not None:
        payload["desired_slot"] = int(desired_slot)

    r = requests.post(url, json=payload, timeout=5)
    r.raise_for_status()
    return r.json()


def locker_commit(region: str, allocation_id: str, locked_until_iso: str | None = None) -> dict:
    base = _base(region).rstrip("/")
    url = f"{base}/locker/allocations/{allocation_id}/commit"
    payload = {"locked_until": locked_until_iso}
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