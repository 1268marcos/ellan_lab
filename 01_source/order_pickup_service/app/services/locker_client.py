# 01_source/order_pickup_service/app/services/locker_client.py
"""
Compat layer para integração com backend regional do locker.

Fonte oficial:
- app.services.backend_client

Regra:
- novos fluxos devem usar backend_client diretamente
- este arquivo existe apenas para evitar divergência e imports legados
"""

from app.services import backend_client


def allocate_slot(region: str, sku_id: str, ttl_sec: int, request_id: str, desired_slot: int | None = None) -> dict:
    return backend_client.locker_allocate(
        region=region,
        sku_id=sku_id,
        ttl_sec=ttl_sec,
        request_id=request_id,
        desired_slot=desired_slot,
    )


def commit_allocation(region: str, allocation_id: str, locked_until_iso: str | None = None) -> dict:
    return backend_client.locker_commit(
        region=region,
        allocation_id=allocation_id,
        locked_until_iso=locked_until_iso,
    )


def release_allocation(region: str, allocation_id: str) -> dict:
    return backend_client.locker_release(
        region=region,
        allocation_id=allocation_id,
    )


def open_slot(region: str, slot: int) -> dict:
    return backend_client.locker_open(
        region=region,
        slot=slot,
    )


def light_on(region: str, slot: int) -> dict:
    return backend_client.locker_light_on(
        region=region,
        slot=slot,
    )


def set_slot_state(region: str, slot: int, state: str, product_id: str | None = None) -> dict:
    return backend_client.locker_set_state(
        region=region,
        slot=slot,
        state=state,
        product_id=product_id,
    )


def open_and_light(region: str, slot: int) -> dict:
    light_resp = backend_client.locker_light_on(region=region, slot=slot)
    open_resp = backend_client.locker_open(region=region, slot=slot)
    return {
        "ok": True,
        "region": region,
        "slot": int(slot),
        "light": light_resp,
        "open": open_resp,
    }