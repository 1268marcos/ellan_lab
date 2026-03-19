from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def send_pickup_ready_email(
    *,
    to_email: str,
    order_id: str,
    token_id: str,
    manual_code: str,
    expires_at: str | None,
    totem_id: str,
) -> None:
    logger.info(
        "pickup_ready_email",
        extra={
            "to_email": to_email,
            "order_id": order_id,
            "token_id": token_id,
            "manual_code": manual_code,
            "expires_at": expires_at,
            "totem_id": totem_id,
        },
    )


def send_pickup_ready_sms(
    *,
    to_phone: str,
    order_id: str,
    manual_code: str,
    expires_at: str | None,
    totem_id: str,
) -> None:
    logger.info(
        "pickup_ready_sms",
        extra={
            "to_phone": to_phone,
            "order_id": order_id,
            "manual_code": manual_code,
            "expires_at": expires_at,
            "totem_id": totem_id,
        },
    )