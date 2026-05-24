from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.advanced import MoneyPlayerPaymentRail
from app.services.crypto_util import new_id


DEFAULT_RAILS: list[dict] = [
    {"player_code": "MAGALU", "country_code": "BR", "payment_method_code": "PIX", "channel": "LOCKER", "max_amount_cents": 5000000},
    {"player_code": "MAGALU", "country_code": "BR", "payment_method_code": "CREDIT_CARD", "channel": "APP"},
    {"player_code": "MERCADOLIVRE", "country_code": "BR", "payment_method_code": "PIX", "channel": "LOCKER"},
    {"player_code": "INPOST", "country_code": "PL", "payment_method_code": "CREDIT_CARD", "channel": "LOCKER"},
    {"player_code": "INPOST", "country_code": "GB", "payment_method_code": "DEBIT_CARD", "channel": "LOCKER"},
    {"player_code": "AMAZON_BR", "country_code": "BR", "payment_method_code": "PIX", "channel": "LOCKER"},
    {"player_code": "WORTEN", "country_code": "PT", "payment_method_code": "CREDIT_CARD", "channel": "LOCKER"},
    {"player_code": "IFOOD", "country_code": "BR", "payment_method_code": "PIX", "channel": "APP", "max_amount_cents": 50000},
    {"player_code": "CORREIOS", "country_code": "BR", "payment_method_code": "PIX", "channel": "LOCKER"},
    {"player_code": "DHL", "country_code": "DE", "payment_method_code": "CREDIT_CARD", "channel": "LOCKER"},
]


def seed_payment_rails(db: Session) -> int:
    n = 0
    for spec in DEFAULT_RAILS:
        pm = spec.get("payment_method_code")
        wp = spec.get("wallet_provider_code")
        ch = spec.get("channel", "LOCKER")
        exists = (
            db.query(MoneyPlayerPaymentRail)
            .filter(
                MoneyPlayerPaymentRail.player_code == spec["player_code"],
                MoneyPlayerPaymentRail.country_code == spec["country_code"],
                MoneyPlayerPaymentRail.payment_method_code == pm,
                MoneyPlayerPaymentRail.wallet_provider_code == wp,
                MoneyPlayerPaymentRail.channel == ch,
            )
            .first()
        )
        if exists:
            continue
        db.add(
            MoneyPlayerPaymentRail(
                id=new_id(),
                player_code=spec["player_code"],
                country_code=spec["country_code"],
                payment_method_code=pm,
                wallet_provider_code=wp,
                channel=ch,
                is_enabled=True,
                max_amount_cents=spec.get("max_amount_cents"),
                notes=spec.get("notes"),
            )
        )
        n += 1
    return n
