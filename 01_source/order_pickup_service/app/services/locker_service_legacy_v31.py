# 01_source/order_pickup_service/app/services/locker_service.py

from __future__ import annotations

import requests
from fastapi import HTTPException
from app.core.config import settings


def _get_runtime_lockers(region: str) -> list[dict]:
    url = f"{settings.payment_gateway_internal.rstrip('/')}/lockers"

    try:
        r = requests.get(
            url,
            params={"region": region, "active_only": True},
            timeout=5,
        )
        r.raise_for_status()
        data = r.json()
        return data.get("items", [])
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail={
                "type": "RUNTIME_LOCKER_FETCH_FAILED",
                "message": "Falha ao consultar runtime lockers via gateway",
                "error": str(e),
            },
        )


def _normalize_methods(methods: list[str]) -> list[str]:
    return [str(m).strip().upper() for m in methods or []]


def _map_payment_method(method: str, card_type: str | None = None) -> list[str]:
    """
    Compatibilidade de domínio sem usar CARD/CASH.

    O runtime/gateway expõe:
    - CARTAO_CREDITO
    - CARTAO_DEBITO
    - CARTAO_PRESENTE
    - NFC
    - PIX
    ...

    O order_pickup_service ainda usa internamente:
    - payment_method = CARTAO
    - card_type = creditCard / debitCard / giftCard
    """

    m = str(method or "").strip().upper()
    ct = str(card_type or "").strip()

    if m == "CARTAO":
        if ct == "creditCard":
            return ["CARTAO_CREDITO"]
        if ct == "debitCard":
            return ["CARTAO_DEBITO"]
        if ct == "giftCard":
            return ["CARTAO_PRESENTE"]
        return ["CARTAO_CREDITO", "CARTAO_DEBITO", "CARTAO_PRESENTE"]

    return [m]


def validate_locker_for_order(
    *,
    db,
    locker_id: str,
    region: str,
    channel: str,
    payment_method: str,
    card_type: str | None = None,
) -> dict:

    lockers = _get_runtime_lockers(region)

    locker = next(
        (l for l in lockers if l.get("locker_id") == locker_id),
        None,
    )

    if not locker:
        raise HTTPException(
            status_code=404,
            detail={
                "type": "LOCKER_NOT_FOUND",
                "message": f"Locker não encontrado: {locker_id}",
                "region": region,
            },
        )

    channels = _normalize_methods(locker.get("channels"))
    if channel not in channels:
        raise HTTPException(
            status_code=409,
            detail={
                "type": "LOCKER_CHANNEL_NOT_ALLOWED",
                "message": f"Canal {channel} não permitido em {locker_id}",
                "allowed_channels": channels,
            },
        )

    raw_methods = (
        locker.get("payment_methods")
        or locker.get("allowed_payment_methods")
        or []
    )

    allowed_methods = _normalize_methods(raw_methods)

    normalized_inputs = _map_payment_method(payment_method, card_type=card_type)

    if not any(m in allowed_methods for m in normalized_inputs):
        raise HTTPException(
            status_code=409,
            detail={
                "type": "LOCKER_PAYMENT_METHOD_NOT_ALLOWED",
                "message": f"Método {payment_method} não permitido em {locker_id}",
                "locker_id": locker_id,
                "allowed_methods": allowed_methods,
                "normalized_input": normalized_inputs,
                "raw_locker": locker, # 🔥 DEBUG CRÍTICO
            },
        )

    return locker