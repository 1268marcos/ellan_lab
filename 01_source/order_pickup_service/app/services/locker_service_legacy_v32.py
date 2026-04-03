# 01_source/order_pickup_service/app/services/locker_service.py
# 02/04/2026

from __future__ import annotations

import requests
from fastapi import HTTPException

from app.core.config import settings


def _get_runtime_lockers(region: str) -> list[dict]:
    url = f"{settings.payment_gateway_internal.rstrip('/')}/lockers"

    try:
        response = requests.get(
            url,
            params={"region": region, "active_only": True},
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("items", [])
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "type": "RUNTIME_LOCKER_FETCH_FAILED",
                "message": "Falha ao consultar runtime lockers via gateway.",
                "error": str(exc),
            },
        ) from exc


def _normalize_upper_list(values: list[str] | None) -> list[str]:
    return [str(v).strip().upper() for v in (values or []) if str(v).strip()]


def _normalize_region(region: str | None) -> str:
    return str(region or "").strip().upper()


def _normalize_channel(channel: str | None) -> str:
    value = str(channel or "").strip().upper()
    aliases = {
        "ONLINE": "ONLINE",
        "WEB": "ONLINE",
        "APP": "ONLINE",
        "KIOSK": "KIOSK",
        "TOTEM": "KIOSK",
    }
    return aliases.get(value, value)


def _map_payment_method_to_locker_capabilities(payment_method: str) -> list[str]:
    """
    Converte o payment_method canônico (opção B) para as capacidades
    hoje expostas pelo locker/gateway/runtime.
    """
    normalized = str(payment_method or "").strip()

    mapping = {
        "creditCard": ["CARTAO_CREDITO"],
        "debitCard": ["CARTAO_DEBITO"],
        "giftCard": ["CARTAO_PRESENTE"],
        "pix": ["PIX"],
        "boleto": ["BOLETO"],
        "apple_pay": ["APPLE_PAY"],
        "google_pay": ["GOOGLE_PAY"],
        "mbway": ["MBWAY"],
        "multibanco_reference": ["MULTIBANCO_REFERENCE"],
        "mercado_pago_wallet": ["MERCADO_PAGO_WALLET"],
    }

    return mapping.get(normalized, [normalized.upper()])


def validate_locker_for_order(
    *,
    db,
    locker_id: str,
    region: str,
    channel: str,
    payment_method: str,
    payment_interface: str | None = None,
) -> dict:
    del db
    del payment_interface

    normalized_region = _normalize_region(region)
    normalized_channel = _normalize_channel(channel)

    lockers = _get_runtime_lockers(normalized_region)

    locker = next(
        (item for item in lockers if item.get("locker_id") == locker_id),
        None,
    )

    if not locker:
        raise HTTPException(
            status_code=404,
            detail={
                "type": "LOCKER_NOT_FOUND",
                "message": f"Locker não encontrado: {locker_id}",
                "locker_id": locker_id,
                "region": normalized_region,
            },
        )

    channels = _normalize_upper_list(locker.get("channels"))
    if normalized_channel not in channels:
        raise HTTPException(
            status_code=409,
            detail={
                "type": "LOCKER_CHANNEL_NOT_ALLOWED",
                "message": f"Canal {normalized_channel} não permitido em {locker_id}",
                "locker_id": locker_id,
                "allowed_channels": channels,
            },
        )

    raw_methods = locker.get("payment_methods") or locker.get("allowed_payment_methods") or []
    allowed_methods = _normalize_upper_list(raw_methods)

    normalized_inputs = _map_payment_method_to_locker_capabilities(payment_method)

    if not any(item in allowed_methods for item in normalized_inputs):
        raise HTTPException(
            status_code=409,
            detail={
                "type": "LOCKER_PAYMENT_METHOD_NOT_ALLOWED",
                "message": f"Método {payment_method} não permitido em {locker_id}",
                "locker_id": locker_id,
                "payment_method": payment_method,
                "allowed_methods": allowed_methods,
                "normalized_input": normalized_inputs,
                "raw_locker": locker,
            },
        )

    return locker