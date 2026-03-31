# 01_source/payment_gateway/app/routers/lockers.py
from __future__ import annotations

import os

import requests
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/lockers", tags=["lockers"])


LOCKER_RUNTIME_INTERNAL = (
    os.getenv("LOCKER_RUNTIME_INTERNAL", "http://backend_runtime:8000").rstrip("/")
)


def _normalize_region(region: str | None) -> str | None:
    if region is None:
        return None
    value = str(region).strip().upper()
    return value or None


def _extract_items(payload) -> list[dict]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict) and isinstance(payload.get("items"), list):
        return [item for item in payload["items"] if isinstance(item, dict)]
    return []


def _safe_address_from_runtime(item: dict) -> dict:
    address = item.get("address")

    if isinstance(address, dict):
        return {
            "address": address.get("address"),
            "number": address.get("number"),
            "additional_information": address.get("additional_information"),
            "locality": address.get("locality"),
            "city": address.get("city"),
            "federative_unit": address.get("federative_unit"),
            "postal_code": address.get("postal_code"),
            "country": address.get("country"),
        }

    return {
        "address": None,
        "number": None,
        "additional_information": None,
        "locality": None,
        "city": item.get("city"),
        "federative_unit": item.get("state"),
        "postal_code": item.get("postal_code"),
        "country": item.get("country"),
    }


def _to_public_summary(item: dict) -> dict:
    locker_id = (
        item.get("locker_id")
        or item.get("id")
        or item.get("machine_id")
        or ""
    )
    locker_id = str(locker_id).strip()

    return {
        "locker_id": locker_id,
        "region": str(item.get("region") or "").strip().upper(),
        "site_id": item.get("site_id"),
        "display_name": item.get("display_name") or locker_id,
        "backend_region": str(item.get("region") or "").strip().upper(),
        "slots": int(item.get("slot_count_total") or item.get("slots_count") or item.get("slots") or 0),
        "channels": list(item.get("allowed_channels") or ["ONLINE", "KIOSK"]),
        "payment_methods": list(item.get("allowed_payment_methods") or []),
        "active": bool(item.get("active", False)),
        "address": _safe_address_from_runtime(item),
    }


def _fetch_runtime_lockers() -> list[dict]:
    url = f"{LOCKER_RUNTIME_INTERNAL}/internal/runtime/lockers"

    internal_token = os.getenv("INTERNAL_SERVICE_TOKEN", "").strip()

    headers = {}
    if internal_token:
        headers["X-Internal-Token"] = internal_token

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=5,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "type": "RUNTIME_LOCKERS_UNAVAILABLE",
                "message": "Falha ao consultar lockers no backend_runtime.",
                "runtime_url": url,
                "error": str(exc),
            },
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "type": "RUNTIME_LOCKERS_INVALID_RESPONSE",
                "message": "Resposta inválida do backend_runtime.",
                "runtime_url": url,
                "error": str(exc),
            },
        ) from exc

    return _extract_items(payload)


@router.get("")
def list_lockers(
    region: str | None = Query(default=None),
    active_only: bool = Query(default=False),
):
    """
    Lista lockers a partir do backend_runtime (fonte canônica).
    """

    normalized_region = _normalize_region(region)
    items = _fetch_runtime_lockers()

    normalized_items = [_to_public_summary(item) for item in items]
    normalized_items = [item for item in normalized_items if item["locker_id"]]

    if normalized_region:
        normalized_items = [
            item for item in normalized_items
            if item["region"] == normalized_region
        ]

    if active_only:
        normalized_items = [
            item for item in normalized_items
            if item["active"] is True
        ]

    normalized_items.sort(
        key=lambda item: (
            item.get("region") or "",
            item.get("display_name") or "",
            item.get("locker_id") or "",
        )
    )

    response = {
        "items": normalized_items,
        "total": len(normalized_items),
    }

    if normalized_region:
        response["region"] = normalized_region

    return response


@router.get("/{locker_id}")
def get_locker(locker_id: str):
    """
    Retorna um locker específico a partir do backend_runtime.
    """
    normalized_locker_id = str(locker_id or "").strip()
    if not normalized_locker_id:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "LOCKER_ID_REQUIRED",
                "message": "locker_id é obrigatório.",
            },
        )

    items = _fetch_runtime_lockers()
    normalized_items = [_to_public_summary(item) for item in items]

    found = next(
        (item for item in normalized_items if item["locker_id"] == normalized_locker_id),
        None,
    )

    if not found:
        raise HTTPException(
            status_code=404,
            detail={
                "type": "LOCKER_NOT_FOUND",
                "message": f"Locker não encontrado: {normalized_locker_id}",
                "locker_id": normalized_locker_id,
            },
        )

    return found