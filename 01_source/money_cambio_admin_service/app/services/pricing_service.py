from __future__ import annotations

from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.advanced import MoneyOpsQuoteLog, MoneyPlayerPaymentRail
from app.models.intelligence import MoneySettlementSchedule
from app.models.professional import (
    CambioCorridorMarkup,
    CambioPaymentCorridor,
    MoneyComplianceLimit,
    MoneyLockerPlayerRegistry,
)
from app.schemas.advanced import PricingLineOut, PricingPreviewIn, PricingPreviewOut
from app.services import fx_service
from app.services.crypto_util import new_id


def _active_markup_bps(db: Session, corridor_id: str, on_date: date | None) -> int:
    ref = on_date or date.today()
    row = (
        db.query(CambioCorridorMarkup)
        .filter(
            CambioCorridorMarkup.corridor_id == corridor_id,
            CambioCorridorMarkup.is_active.is_(True),
            CambioCorridorMarkup.valid_from <= ref,
        )
        .order_by(CambioCorridorMarkup.valid_from.desc())
        .first()
    )
    if not row:
        return 0
    if row.valid_until and row.valid_until < ref:
        return 0
    return int(row.markup_bps or 0)


def _check_compliance(db: Session, country: str, currency: str, amount_cents: int) -> tuple[str, list[str]]:
    notes: list[str] = []
    limits = (
        db.query(MoneyComplianceLimit)
        .filter(
            MoneyComplianceLimit.country_code == country,
            MoneyComplianceLimit.currency_code == currency,
            MoneyComplianceLimit.is_active.is_(True),
        )
        .all()
    )
    if not limits:
        return "UNKNOWN", ["Nenhum limite AML/KYC cadastrado para o país."]
    for lim in limits:
        if amount_cents > lim.amount_cents:
            notes.append(f"Excede {lim.limit_type}: {lim.amount_cents} {lim.currency_code}")
    if notes:
        return "BLOCKED", notes
    return "OK", []


def _rail_allowed(
    db: Session,
    *,
    player_code: str,
    country: str,
    payment_method: str | None,
) -> bool:
    q = db.query(MoneyPlayerPaymentRail).filter(
        MoneyPlayerPaymentRail.player_code == player_code,
        MoneyPlayerPaymentRail.country_code == country,
        MoneyPlayerPaymentRail.is_enabled.is_(True),
    )
    rails = q.all()
    if not rails:
        return True  # sem rails cadastrados = permite (modo permissivo OPS)
    if not payment_method:
        return True
    return any(r.payment_method_code == payment_method for r in rails if r.payment_method_code)


def preview_pricing(db: Session, body: PricingPreviewIn) -> PricingPreviewOut:
    player = (
        db.query(MoneyLockerPlayerRegistry)
        .filter(MoneyLockerPlayerRegistry.player_code == body.player_code.upper())
        .first()
    )
    if not player:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="player_not_found")

    country = (body.country_code or player.primary_country).upper()
    corridor: CambioPaymentCorridor | None = None
    if body.corridor_code:
        corridor = (
            db.query(CambioPaymentCorridor)
            .filter(CambioPaymentCorridor.corridor_code == body.corridor_code.upper())
            .first()
        )
    elif player.cambio_corridor_code:
        corridor = (
            db.query(CambioPaymentCorridor)
            .filter(CambioPaymentCorridor.corridor_code == player.cambio_corridor_code)
            .first()
        )

    tx_ccy = corridor.transaction_currency if corridor else player.default_settlement_currency
    settle_ccy = corridor.settlement_currency if corridor else player.default_settlement_currency
    spread_bps = int(corridor.default_spread_bps) if corridor else 0
    markup_bps = _active_markup_bps(db, corridor.id, body.on_date) if corridor else 0

    warnings: list[str] = []
    if not corridor:
        warnings.append("Corredor não encontrado; usando moeda de settlement do player.")

    fx = fx_service.convert_cents(db, body.amount_cents, tx_ccy, settle_ccy, body.on_date)
    base_settle = fx["to_amount_cents"]
    total_bps = spread_bps + markup_bps
    fee_cents = int(
        (Decimal(base_settle) * Decimal(total_bps) / Decimal(10000)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    )
    settlement_cents = base_settle + fee_cents

    compliance_status, compliance_notes = _check_compliance(db, country, settle_ccy, settlement_cents)
    rail_ok = _rail_allowed(db, player_code=player.player_code, country=country, payment_method=body.payment_method_code)

    scope_codes = [player.player_code]
    if corridor:
        scope_codes.append(corridor.corridor_code)
    schedule = (
        db.query(MoneySettlementSchedule)
        .filter(
            MoneySettlementSchedule.is_active.is_(True),
            MoneySettlementSchedule.scope_code.in_(scope_codes),
            MoneySettlementSchedule.country_code == country,
        )
        .first()
    )

    lines = [
        PricingLineOut(label="Valor transação", amount_cents=body.amount_cents, currency=tx_ccy),
        PricingLineOut(
            label="FX spot",
            amount_cents=base_settle,
            currency=settle_ccy,
            detail=f"rate {fx.get('rate')} @ {fx.get('rate_date')}",
        ),
        PricingLineOut(label="Spread corredor", bps=spread_bps, detail=f"{spread_bps} bps"),
        PricingLineOut(label="Markup parceiro", bps=markup_bps, detail=f"{markup_bps} bps"),
        PricingLineOut(label="Taxa total FX+", amount_cents=fee_cents, currency=settle_ccy),
        PricingLineOut(label="Settlement líquido", amount_cents=settlement_cents, currency=settle_ccy),
    ]

    if body.payment_method_code and not rail_ok:
        warnings.append(f"Método {body.payment_method_code} não habilitado no rail do player.")

    out = PricingPreviewOut(
        player_code=player.player_code,
        corridor_code=corridor.corridor_code if corridor else None,
        transaction_currency=tx_ccy,
        settlement_currency=settle_ccy,
        amount_cents=body.amount_cents,
        fx_rate=fx.get("rate"),
        fx_rate_date=fx.get("rate_date"),
        spread_bps=spread_bps,
        markup_bps=markup_bps,
        settlement_cents=settlement_cents,
        settlement_days=schedule.settlement_days if schedule else None,
        cut_off_time_utc=schedule.cut_off_time_utc if schedule else None,
        compliance_status=compliance_status,
        compliance_notes=compliance_notes,
        rail_allowed=rail_ok,
        lines=lines,
        warnings=warnings,
    )

    db.add(
        MoneyOpsQuoteLog(
            id=new_id(),
            quote_type="PRICING_PREVIEW",
            player_code=player.player_code,
            corridor_code=corridor.corridor_code if corridor else None,
            request_json=body.model_dump(mode="json"),
            result_json=out.model_dump(mode="json"),
        )
    )
    db.commit()
    return out
