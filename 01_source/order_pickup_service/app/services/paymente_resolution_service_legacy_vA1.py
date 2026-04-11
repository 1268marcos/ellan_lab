# 01_source/order_pickup_service/app/services/payment_resolution_service.py
# 06/04/2026

from __future__ import annotations

from typing import Any, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.payment_method_ui_alias import PaymentMethodUiAlias


def resolve_payment_ui_code(
    *,
    db: Session,
    raw_payment_method: Any,
    raw_payment_interface: Any = None,
    raw_wallet_provider: Any = None,
) -> dict:
    raw_method = str(raw_payment_method or "").strip()
    if not raw_method:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "INVALID_PAYMENT_METHOD",
                "message": "payment_method é obrigatório.",
            },
        )

    alias = (
        db.query(PaymentMethodUiAlias)
        .filter(
            PaymentMethodUiAlias.is_active.is_(True),
            PaymentMethodUiAlias.ui_code == raw_method.upper(),
        )
        .first()
    )

    if alias is None:
        return {
            "payment_method": raw_method,
            "payment_interface": str(raw_payment_interface).strip() if raw_payment_interface else None,
            "wallet_provider": str(raw_wallet_provider).strip() if raw_wallet_provider else None,
            "requires_customer_phone": False,
            "requires_wallet_provider": False,
            "resolved_from_ui_code": False,
        }

    payment_interface = (
        str(raw_payment_interface).strip()
        if raw_payment_interface is not None and str(raw_payment_interface).strip()
        else alias.default_payment_interface_code
    )

    wallet_provider = (
        str(raw_wallet_provider).strip()
        if raw_wallet_provider is not None and str(raw_wallet_provider).strip()
        else alias.default_wallet_provider_code
    )

    return {
        "payment_method": alias.canonical_method_code,
        "payment_interface": payment_interface,
        "wallet_provider": wallet_provider,
        "requires_customer_phone": bool(alias.requires_customer_phone),
        "requires_wallet_provider": bool(alias.requires_wallet_provider),
        "resolved_from_ui_code": True,
        "ui_code": alias.ui_code,
    }
