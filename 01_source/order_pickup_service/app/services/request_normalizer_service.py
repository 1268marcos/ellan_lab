# 01_source/order_pickup_service/app/services/request_normalizer_service.py
# 12/04/2026 - criação de NORMALIZER SERVICE (sincrono, seguro)

def normalize_payment_payload(db, payload: dict) -> dict:
    from app.services.payment_resolution_service import resolve_payment_ui_code
    from app.services import backend_client

    # ===============================
    # 1. PAYMENT METHOD
    # ===============================
    if payload.get("payment_method"):
        resolved = resolve_payment_ui_code(
            db=db,
            raw_payment_method=payload.get("payment_method"),
            raw_payment_interface=payload.get("payment_interface"),
            raw_wallet_provider=payload.get("wallet_provider"),
        )

        payload["payment_method"] = resolved.get("payment_method")
        payload["payment_interface"] = resolved.get("payment_interface")
        payload["wallet_provider"] = resolved.get("wallet_provider")

    # ===============================
    # 2. SLOT
    # ===============================
    if payload.get("desired_slot") is not None:
        payload["desired_slot"] = int(payload["desired_slot"])

    # ===============================
    # 3. AMOUNT (KIOSK)
    # ===============================
    if payload.get("payment_method") in {"creditCard", "debitCard"}:
        if not payload.get("amount_cents"):
            pricing = backend_client.get_sku_pricing(
                payload.get("region"),
                payload.get("sku_id"),
                locker_id=payload.get("totem_id"),
            )

            payload["amount_cents"] = int(
                pricing.get("amount_cents")
                or pricing.get("price_cents")
            )

    return payload

