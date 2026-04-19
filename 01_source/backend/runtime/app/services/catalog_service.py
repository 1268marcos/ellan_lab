# 01_source/backend/runtime/app/services/catalog_service.py
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException

from app.core.locker_runtime_resolver import resolve_runtime_locker
from app.core.slot_topology import get_valid_slot_ids
from app.schemas.catalog import CatalogSkuOut, CatalogSlotOut

from app.core.datetime_utils import to_iso_utc



def _build_error(
    *,
    err_type: str,
    message: str,
    retryable: bool,
    **extra,
) -> dict:
    detail = {
        "type": err_type,
        "message": message,
        "retryable": retryable,
    }
    if extra:
        detail.update(extra)
    return detail


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_sku_catalog() -> dict[str, dict[str, Any]]:
    """
    Catálogo transitório para desenvolvimento.
    O catálogo definitivo deve migrar para fonte central.
    """
    return {
        "cookie_laranja": {
            "name": "Cookie de Laranja",
            "amount_cents": 4850,
            "currency": "BRL",
            "imageURL": "",
            "is_active": True,
        },
        "cookie_cenoura": {
            "name": "Cookie de Cenoura",
            "amount_cents": 4990,
            "currency": "BRL",
            "imageURL": "",
            "is_active": True,
        },
        "mini_cookie_iogurte": {
            "name": "Mini Cookie de Iogurte",
            "amount_cents": 4495,
            "currency": "BRL",
            "imageURL": "",
            "is_active": True,
        },
        "cookie_especial": {
            "name": "Cookie Especial",
            "amount_cents": 4889,
            "currency": "BRL",
            "imageURL": "",
            "is_active": True,
        },
        "cookie_canetinha": {
            "name": "Cookie Canetinha",
            "amount_cents": 11099,
            "currency": "BRL",
            "imageURL": "",
            "is_active": True,
        },
    }


def _load_json_env(var_name: str) -> Any | None:
    raw = os.getenv(var_name)
    if not raw:
        return None

    try:
        return json.loads(raw)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=_build_error(
                err_type="INVALID_JSON_ENV",
                message=f"{var_name} is not valid JSON.",
                retryable=False,
                env_var=var_name,
                error=str(exc),
            ),
        ) from exc


def _load_sku_catalog() -> dict[str, dict[str, Any]]:
    """
    Fonte transitória do catálogo:
    1. RUNTIME_SKU_CATALOG_JSON
    2. fallback interno para desenvolvimento

    Estrutura esperada:
    {
      "sku_id": {
        "name": "...",
        "amount_cents": 1234,
        "currency": "BRL",
        "imageURL": "",
        "is_active": true
      }
    }
    """
    env_data = _load_json_env("RUNTIME_SKU_CATALOG_JSON")
    if env_data is None:
        env_data = _default_sku_catalog()

    if not isinstance(env_data, dict):
        raise HTTPException(
            status_code=500,
            detail=_build_error(
                err_type="INVALID_SKU_CATALOG",
                message="RUNTIME_SKU_CATALOG_JSON must be a JSON object keyed by sku_id.",
                retryable=False,
                parsed_type=type(env_data).__name__,
            ),
        )

    normalized: dict[str, dict[str, Any]] = {}

    for sku_id, item in env_data.items():
        if not isinstance(item, dict):
            raise HTTPException(
                status_code=500,
                detail=_build_error(
                    err_type="INVALID_SKU_ITEM",
                    message="Each SKU entry must be an object.",
                    retryable=False,
                    sku_id=sku_id,
                    parsed_type=type(item).__name__,
                ),
            )

        try:
            normalized[str(sku_id)] = {
                "name": str(item["name"]),
                "amount_cents": int(item["amount_cents"]),
                "currency": str(item.get("currency", "BRL")),
                "imageURL": str(item.get("imageURL", "")),
                "is_active": bool(item.get("is_active", True)),
            }
        except KeyError as exc:
            raise HTTPException(
                status_code=500,
                detail=_build_error(
                    err_type="SKU_FIELD_REQUIRED",
                    message="A required field is missing in SKU catalog.",
                    retryable=False,
                    sku_id=sku_id,
                    missing_field=str(exc),
                ),
            ) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=_build_error(
                    err_type="INVALID_SKU_ITEM",
                    message="SKU entry contains invalid field values.",
                    retryable=False,
                    sku_id=sku_id,
                    error=str(exc),
                ),
            ) from exc

    if not normalized:
        raise HTTPException(
            status_code=503,
            detail=_build_error(
                err_type="EMPTY_SKU_CATALOG",
                message="No SKU catalog is available.",
                retryable=False,
            ),
        )

    return normalized


def _active_sku_ids(sku_catalog: dict[str, dict[str, Any]]) -> list[str]:
    return [sku_id for sku_id, item in sku_catalog.items() if bool(item.get("is_active", True))]


def _load_locker_slot_plan_map() -> dict[str, dict[int, str]]:
    """
    Fonte transitória do plano por locker:
    ENV: RUNTIME_LOCKER_SLOT_PLAN_JSON

    Estrutura esperada:
    {
      "LOCKER_ID": {
        "1": "sku_a",
        "2": "sku_b"
      }
    }
    """
    env_data = _load_json_env("RUNTIME_LOCKER_SLOT_PLAN_JSON")
    if env_data is None:
        return {}

    if not isinstance(env_data, dict):
        raise HTTPException(
            status_code=500,
            detail=_build_error(
                err_type="INVALID_LOCKER_SLOT_PLAN",
                message="RUNTIME_LOCKER_SLOT_PLAN_JSON must be a JSON object keyed by locker_id.",
                retryable=False,
                parsed_type=type(env_data).__name__,
            ),
        )

    normalized: dict[str, dict[int, str]] = {}

    for locker_id, mapping in env_data.items():
        if not isinstance(mapping, dict):
            raise HTTPException(
                status_code=500,
                detail=_build_error(
                    err_type="INVALID_LOCKER_SLOT_PLAN_ITEM",
                    message="Each locker slot plan must be an object keyed by slot number.",
                    retryable=False,
                    locker_id=locker_id,
                    parsed_type=type(mapping).__name__,
                ),
            )

        slot_map: dict[int, str] = {}
        for slot_raw, sku_id in mapping.items():
            try:
                slot_int = int(slot_raw)
            except Exception as exc:
                raise HTTPException(
                    status_code=500,
                    detail=_build_error(
                        err_type="INVALID_SLOT_KEY",
                        message="Slot keys in locker slot plan must be integers.",
                        retryable=False,
                        locker_id=locker_id,
                        slot_key=slot_raw,
                        error=str(exc),
                    ),
                ) from exc

            slot_map[slot_int] = str(sku_id)

        normalized[str(locker_id)] = slot_map

    return normalized


def _generate_deterministic_slot_plan(
    *,
    locker_id: str,
    slot_ids: list[int],
    active_sku_ids: list[str],
) -> dict[int, str]:
    """
    Fallback profissional:
    se não houver plano explícito para o locker, distribui SKUs ativos
    de forma determinística sobre a topologia válida do locker.
    """
    if not active_sku_ids:
        raise HTTPException(
            status_code=503,
            detail=_build_error(
                err_type="NO_ACTIVE_SKUS",
                message="There are no active SKUs available to project into slots.",
                retryable=False,
                locker_id=locker_id,
            ),
        )

    plan: dict[int, str] = {}
    for idx, slot in enumerate(sorted(slot_ids)):
        plan[int(slot)] = active_sku_ids[idx % len(active_sku_ids)]

    return plan


def _resolve_slot_plan_for_locker(
    *,
    locker_id: str,
    slot_ids: list[int],
    sku_catalog: dict[str, dict[str, Any]],
) -> dict[int, str]:
    explicit_map = _load_locker_slot_plan_map()
    active_ids = _active_sku_ids(sku_catalog)

    if locker_id not in explicit_map:
        return _generate_deterministic_slot_plan(
            locker_id=locker_id,
            slot_ids=slot_ids,
            active_sku_ids=active_ids,
        )

    plan = explicit_map[locker_id]

    valid_slots = set(slot_ids)
    active_skus = set(active_ids)

    # Validação profissional do plano explícito
    for slot, sku_id in plan.items():
        if slot not in valid_slots:
            raise HTTPException(
                status_code=500,
                detail=_build_error(
                    err_type="LOCKER_SLOT_PLAN_INVALID_SLOT",
                    message="Locker slot plan contains a slot not present in locker topology.",
                    retryable=False,
                    locker_id=locker_id,
                    slot=slot,
                    valid_slots=sorted(valid_slots),
                ),
            )

        if sku_id not in sku_catalog:
            raise HTTPException(
                status_code=500,
                detail=_build_error(
                    err_type="LOCKER_SLOT_PLAN_UNKNOWN_SKU",
                    message="Locker slot plan references an unknown SKU.",
                    retryable=False,
                    locker_id=locker_id,
                    slot=slot,
                    sku_id=sku_id,
                ),
            )

        if sku_id not in active_skus:
            raise HTTPException(
                status_code=500,
                detail=_build_error(
                    err_type="LOCKER_SLOT_PLAN_INACTIVE_SKU",
                    message="Locker slot plan references an inactive SKU.",
                    retryable=False,
                    locker_id=locker_id,
                    slot=slot,
                    sku_id=sku_id,
                ),
            )

    # Política profissional:
    # completa slots faltantes usando distribuição determinística
    if set(plan.keys()) != valid_slots:
        generated = _generate_deterministic_slot_plan(
            locker_id=locker_id,
            slot_ids=slot_ids,
            active_sku_ids=active_ids,
        )
        merged = dict(generated)
        merged.update(plan)
        return merged

    return dict(plan)


def _build_sku_out(*, locker_id: str, sku_id: str, item: dict[str, Any]) -> CatalogSkuOut:
    return CatalogSkuOut(
        locker_id=locker_id,
        sku_id=sku_id,
        name=str(item["name"]),
        amount_cents=int(item["amount_cents"]),
        currency=str(item.get("currency", "BRL")),
        imageURL=str(item.get("imageURL", "")),
        is_active=bool(item.get("is_active", True)),
        updated_at=_now_iso(),
    )


def _build_slot_out(
    *,
    locker_id: str,
    slot: int,
    sku_id: str | None,
    item: dict[str, Any] | None,
) -> CatalogSlotOut:
    return CatalogSlotOut(
        locker_id=locker_id,
        slot=int(slot),
        sku_id=sku_id,
        name=item["name"] if item else None,
        amount_cents=int(item["amount_cents"]) if item else None,
        currency=str(item.get("currency", "BRL")) if item else "BRL",
        imageURL=str(item.get("imageURL", "")) if item else "",
        is_active=bool(item.get("is_active", True)) if item else False,
        updated_at=_now_iso(),
    )


def list_catalog_skus(*, x_locker_id: str | None) -> list[CatalogSkuOut]:
    locker_ctx = resolve_runtime_locker(x_locker_id)
    locker_id = locker_ctx["locker_id"]

    sku_catalog = _load_sku_catalog()

    return [
        _build_sku_out(locker_id=locker_id, sku_id=sku_id, item=item)
        for sku_id, item in sku_catalog.items()
        if bool(item.get("is_active", True))
    ]


def get_catalog_sku(*, x_locker_id: str | None, sku_id: str) -> CatalogSkuOut:
    locker_ctx = resolve_runtime_locker(x_locker_id)
    locker_id = locker_ctx["locker_id"]

    sku_catalog = _load_sku_catalog()
    item = sku_catalog.get(sku_id)

    if not item or not bool(item.get("is_active", True)):
        raise HTTPException(
            status_code=404,
            detail=_build_error(
                err_type="SKU_NOT_FOUND",
                message="SKU not found or inactive for this runtime.",
                retryable=False,
                locker_id=locker_id,
                sku_id=sku_id,
            ),
        )

    return _build_sku_out(locker_id=locker_id, sku_id=sku_id, item=item)


def list_catalog_slots(*, x_locker_id: str | None) -> list[CatalogSlotOut]:
    locker_ctx = resolve_runtime_locker(x_locker_id)
    locker_id = locker_ctx["locker_id"]

    slot_ids = get_valid_slot_ids(locker_ctx)
    sku_catalog = _load_sku_catalog()

    slot_plan = _resolve_slot_plan_for_locker(
        locker_id=locker_id,
        slot_ids=slot_ids,
        sku_catalog=sku_catalog,
    )

    items: list[CatalogSlotOut] = []

    for slot in sorted(slot_ids):
        sku_id = slot_plan.get(int(slot))
        sku_item = sku_catalog.get(sku_id) if sku_id else None

        if sku_item and not bool(sku_item.get("is_active", True)):
            sku_id = None
            sku_item = None

        items.append(
            _build_slot_out(
                locker_id=locker_id,
                slot=int(slot),
                sku_id=sku_id,
                item=sku_item,
            )
        )

    return items