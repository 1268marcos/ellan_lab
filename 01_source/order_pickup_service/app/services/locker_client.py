# Cliente HTTP para falar com backend SP/PT (PROPOSTO) - Aqui é onde você vai validar nomes de rotas.
import requests
from app.core.config import settings

def _base_for_region(region: str) -> str:
    return settings.backend_sp_internal if region == "SP" else settings.backend_pt_internal

def allocate_slot(region: str, sku_id: str, ttl_sec: int, request_id: str) -> dict:
    """
    (PROPOSTO) POST /locker/allocate
    """
    url = _base_for_region(region) + "/locker/allocate"
    r = requests.post(url, json={"sku_id": sku_id, "ttl_sec": ttl_sec, "request_id": request_id}, timeout=5)
    r.raise_for_status()
    return r.json()

def commit_allocation(region: str, allocation_id: str, order_id: str, pickup_deadline_at_iso: str) -> dict:
    """
    (PROPOSTO) POST /locker/allocations/{id}/commit
    """
    url = _base_for_region(region) + f"/locker/allocations/{allocation_id}/commit"
    r = requests.post(url, json={"order_id": order_id, "pickup_deadline_at": pickup_deadline_at_iso}, timeout=5)
    r.raise_for_status()
    return r.json()

def open_and_light(region: str, slot: int) -> None:
    """
    (PROPOSTO) POST /locker/slots/{slot}/open and /light/on
    """
    base = _base_for_region(region)
    requests.post(base + f"/locker/slots/{slot}/open", timeout=5).raise_for_status()
    requests.post(base + f"/locker/slots/{slot}/light/on", timeout=5).raise_for_status()
    
# acima (trecho)
