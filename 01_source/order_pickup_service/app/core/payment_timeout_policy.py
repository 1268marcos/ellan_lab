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
    if not value:
        return "DEFAULT"
    return value


def _norm_order_channel(order_channel: str | None) -> str:
    value = (order_channel or "").strip().upper()

    aliases = {
        "KIOSK": "KIOSK",
        "TOTEM": "KIOSK",
        "PRESENTIAL": "KIOSK",
        "IN_PERSON": "KIOSK",
        "ONLINE": "ONLINE",
        "WEB": "ONLINE",
        "APP": "ONLINE",
        "MOBILE": "ONLINE",
    }

    return aliases.get(value, value or "DEFAULT")


def _norm_payment_method(payment_method: str | None) -> str:
    value = (payment_method or "").strip().upper()

    aliases = {
        # PIX
        "PIX": "PIX",

        # cartão
        "CARD": "CARD",
        "CREDIT_CARD": "CARD",
        "DEBIT_CARD": "CARD",
        "CREDITCARD": "CARD",
        "DEBITCARD": "CARD",
        "CARTAO": "CARD",
        "CARTÃO": "CARD",
        "CARTAO_CREDITO": "CARD",
        "CARTAO_DEBITO": "CARD",
        "CARTÃO_CRÉDITO": "CARD",
        "CARTÃO_DÉBITO": "CARD",

        # PT
        "MBWAY": "MBWAY",
        "MB_WAY": "MBWAY",
        "MULTIBANCO_REFERENCE": "MULTIBANCO_REFERENCE",
        "MULTIBANCO": "MULTIBANCO_REFERENCE",
        "REFERENCIA_MULTIBANCO": "MULTIBANCO_REFERENCE",
        "REFERÊNCIA_MULTIBANCO": "MULTIBANCO_REFERENCE",

        # instantâneos / wallets / aproximação
        "NFC": "NFC",
        "APPLE_PAY": "APPLE_PAY",
        "GOOGLE_PAY": "GOOGLE_PAY",
        "MERCADO_PAGO_WALLET": "MERCADO_PAGO_WALLET",
        "MERCADOPAGO_WALLET": "MERCADO_PAGO_WALLET",
        "MERCADO_PAGO": "MERCADO_PAGO_WALLET",
        "MERCADOPAGO": "MERCADO_PAGO_WALLET",
    }

    return aliases.get(value, value or "DEFAULT")


def _wallet_family_timeout_seconds(payment_method: str) -> int | None:
    if payment_method in {
        "NFC",
        "APPLE_PAY",
        "GOOGLE_PAY",
        "MERCADO_PAGO_WALLET",
    }:
        return 10
    return None


# Política explícita aprovada
#
# SP
# - KIOSK PIX: 5 min
# - ONLINE PIX: 6 min
# - KIOSK cartão: 2 min
# - ONLINE cartão: 2 min
# - NFC / APPLE PAY / GOOGLE PAY / MERCADO_PAGO_WALLET: 10 s
#
# PT
# - KIOSK MB WAY: 2 min
# - KIOSK MULTIBANCO_REFERENCE: 5 min
# - ONLINE MBWAY / MULTIBANCO_REFERENCE: 6 min
# - KIOSK cartão: 2 min
# - ONLINE cartão: 2 min
# - NFC / APPLE_PAY / GOOGLE_PAY: 10 s
#
# Observação:
# para métodos instantâneos/wallets, a regra é transversal por região/canal.
_POLICY_SECONDS: dict[TimeoutPolicyKey, int] = {
    # SP
    TimeoutPolicyKey("SP", "KIOSK", "PIX"): 5 * 60,
    TimeoutPolicyKey("SP", "ONLINE", "PIX"): 6 * 60,
    TimeoutPolicyKey("SP", "KIOSK", "CARD"): 2 * 60,
    TimeoutPolicyKey("SP", "ONLINE", "CARD"): 2 * 60,

    # PT
    TimeoutPolicyKey("PT", "KIOSK", "MBWAY"): 2 * 60,
    TimeoutPolicyKey("PT", "KIOSK", "MULTIBANCO_REFERENCE"): 5 * 60,
    TimeoutPolicyKey("PT", "ONLINE", "MBWAY"): 6 * 60,
    TimeoutPolicyKey("PT", "ONLINE", "MULTIBANCO_REFERENCE"): 6 * 60,
    TimeoutPolicyKey("PT", "KIOSK", "CARD"): 2 * 60,
    TimeoutPolicyKey("PT", "ONLINE", "CARD"): 2 * 60,
}


def resolve_prepayment_timeout_seconds(
    *,
    region_code: str | None,
    order_channel: str,
    payment_method: str | None,
) -> int:
    """
    Resolve o timeout pré-pagamento em segundos de forma centralizada.

    Ordem de resolução:
    1. normaliza região/canal/método
    2. aplica família instantânea (NFC / wallets) = 10s
    3. procura regra exata por região + canal + método
    4. aplica fallback por método conhecido
    5. aplica fallback global conservador
    """

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

    # Fallbacks profissionais para evitar comportamento imprevisível
    if norm_method == "PIX":
        if norm_channel == "KIOSK":
            return 5 * 60
        if norm_channel == "ONLINE":
            return 6 * 60

    if norm_method == "CARD":
        return 2 * 60

    if norm_method == "MBWAY":
        if norm_channel == "KIOSK":
            return 2 * 60
        if norm_channel == "ONLINE":
            return 6 * 60

    if norm_method == "MULTIBANCO_REFERENCE":
        if norm_channel == "KIOSK":
            return 5 * 60
        if norm_channel == "ONLINE":
            return 6 * 60

    return DEFAULT_PREPAYMENT_TIMEOUT_SECONDS