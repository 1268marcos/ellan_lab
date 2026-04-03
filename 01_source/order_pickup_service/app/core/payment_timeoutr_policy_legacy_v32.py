# 01_source/order_pickup_service/app/core/payment_timeout_policy.py
# 02/04/2026

from __future__ import annotations

from dataclasses import dataclass


DEFAULT_PREPAYMENT_TIMEOUT_SECONDS = 5 * 60


@dataclass(frozen=True)
class TimeoutPolicyKey:
    region_code: str
    order_channel: str
    payment_method: str


def _norm_region_code(region_code: str | None) -> str:
    value = (region_code or "").strip().upper()
    return value or "DEFAULT"


def _norm_order_channel(order_channel: str | None) -> str:
    value = (order_channel or "").strip().lower()

    aliases = {
        "kiosk": "KIOSK",
        "totem": "KIOSK",
        "presential": "KIOSK",
        "in_person": "KIOSK",
        "online": "ONLINE",
        "web": "ONLINE",
        "app": "ONLINE",
        "mobile": "ONLINE",
    }

    return aliases.get(value, value.upper() or "DEFAULT")


def _norm_payment_method(payment_method: str | None) -> str:
    value = (payment_method or "").strip()

    aliases = {
        "creditCard": "CREDIT_CARD",
        "debitCard": "DEBIT_CARD",
        "giftCard": "GIFT_CARD",
        "pix": "PIX",
        "boleto": "BOLETO",
        "apple_pay": "APPLE_PAY",
        "google_pay": "GOOGLE_PAY",
        "mbway": "MBWAY",
        "multibanco_reference": "MULTIBANCO_REFERENCE",
        "mercado_pago_wallet": "MERCADO_PAGO_WALLET",

        # aliases defensivos
        "CREDIT_CARD": "CREDIT_CARD",
        "DEBIT_CARD": "DEBIT_CARD",
        "GIFT_CARD": "GIFT_CARD",
        "PIX": "PIX",
        "BOLETO": "BOLETO",
        "APPLE_PAY": "APPLE_PAY",
        "GOOGLE_PAY": "GOOGLE_PAY",
        "MBWAY": "MBWAY",
        "MULTIBANCO_REFERENCE": "MULTIBANCO_REFERENCE",
        "MERCADO_PAGO_WALLET": "MERCADO_PAGO_WALLET",
    }

    return aliases.get(value, value.upper() or "DEFAULT")


def _wallet_family_timeout_seconds(payment_method: str) -> int | None:
    if payment_method in {
        "APPLE_PAY",
        "GOOGLE_PAY",
        "MERCADO_PAGO_WALLET",
    }:
        return 10
    return None


_POLICY_SECONDS: dict[TimeoutPolicyKey, int] = {
    TimeoutPolicyKey("SP", "KIOSK", "PIX"): 5 * 60,
    TimeoutPolicyKey("SP", "ONLINE", "PIX"): 6 * 60,

    TimeoutPolicyKey("SP", "KIOSK", "CREDIT_CARD"): 2 * 60,
    TimeoutPolicyKey("SP", "ONLINE", "CREDIT_CARD"): 2 * 60,
    TimeoutPolicyKey("SP", "KIOSK", "DEBIT_CARD"): 2 * 60,
    TimeoutPolicyKey("SP", "ONLINE", "DEBIT_CARD"): 2 * 60,
    TimeoutPolicyKey("SP", "KIOSK", "GIFT_CARD"): 2 * 60,
    TimeoutPolicyKey("SP", "ONLINE", "GIFT_CARD"): 2 * 60,

    TimeoutPolicyKey("PT", "KIOSK", "MBWAY"): 2 * 60,
    TimeoutPolicyKey("PT", "ONLINE", "MBWAY"): 6 * 60,

    TimeoutPolicyKey("PT", "KIOSK", "MULTIBANCO_REFERENCE"): 5 * 60,
    TimeoutPolicyKey("PT", "ONLINE", "MULTIBANCO_REFERENCE"): 6 * 60,

    TimeoutPolicyKey("PT", "KIOSK", "CREDIT_CARD"): 2 * 60,
    TimeoutPolicyKey("PT", "ONLINE", "CREDIT_CARD"): 2 * 60,
    TimeoutPolicyKey("PT", "KIOSK", "DEBIT_CARD"): 2 * 60,
    TimeoutPolicyKey("PT", "ONLINE", "DEBIT_CARD"): 2 * 60,
    TimeoutPolicyKey("PT", "KIOSK", "GIFT_CARD"): 2 * 60,
    TimeoutPolicyKey("PT", "ONLINE", "GIFT_CARD"): 2 * 60,
}


def resolve_prepayment_timeout_seconds(
    *,
    region_code: str | None,
    order_channel: str,
    payment_method: str | None,
) -> int:
    norm_region = _norm_region_code(region_code)
    norm_channel = _norm_order_channel(order_channel)
    norm_method = _norm_payment_method(payment_method)

    wallet_timeout = _wallet_family_timeout_seconds(norm_method)
    if wallet_timeout is not None:
        return wallet_timeout

    exact_key = TimeoutPolicyKey(norm_region, norm_channel, norm_method)
    exact_timeout = _POLICY_SECONDS.get(exact_key)
    if exact_timeout is not None:
        return exact_timeout

    if norm_method == "PIX":
        return 5 * 60 if norm_channel == "KIOSK" else 6 * 60 if norm_channel == "ONLINE" else DEFAULT_PREPAYMENT_TIMEOUT_SECONDS

    if norm_method in {"CREDIT_CARD", "DEBIT_CARD", "GIFT_CARD"}:
        return 2 * 60

    if norm_method == "MBWAY":
        return 2 * 60 if norm_channel == "KIOSK" else 6 * 60 if norm_channel == "ONLINE" else DEFAULT_PREPAYMENT_TIMEOUT_SECONDS

    if norm_method == "MULTIBANCO_REFERENCE":
        return 5 * 60 if norm_channel == "KIOSK" else 6 * 60 if norm_channel == "ONLINE" else DEFAULT_PREPAYMENT_TIMEOUT_SECONDS

    if norm_method == "BOLETO":
        return 15 * 60

    return DEFAULT_PREPAYMENT_TIMEOUT_SECONDS