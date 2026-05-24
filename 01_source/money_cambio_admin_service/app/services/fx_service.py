from __future__ import annotations

from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.cambio import CambioFxRate
from app.schemas.cambio import FxRateIn
from app.services.crypto_util import new_id


def list_fx_rates(db: Session, base: str | None = None, quote: str | None = None) -> list[CambioFxRate]:
    q = db.query(CambioFxRate).order_by(CambioFxRate.rate_date.desc())
    if base:
        q = q.filter(CambioFxRate.base_currency == base.upper())
    if quote:
        q = q.filter(CambioFxRate.quote_currency == quote.upper())
    return q.limit(200).all()


def upsert_fx_rate(db: Session, body: FxRateIn) -> CambioFxRate:
    base = body.base_currency.upper()
    quote = body.quote_currency.upper()
    existing = (
        db.query(CambioFxRate)
        .filter(
            CambioFxRate.base_currency == base,
            CambioFxRate.quote_currency == quote,
            CambioFxRate.rate_date == body.rate_date,
        )
        .first()
    )
    old_rate = existing.rate if existing else None
    if existing:
        existing.rate = body.rate
        existing.source = body.source
        row = existing
    else:
        row = CambioFxRate(
            id=new_id(),
            base_currency=base,
            quote_currency=quote,
            rate_date=body.rate_date,
            rate=body.rate,
            source=body.source,
        )
        db.add(row)
    from app.services.professional_service import record_fx_audit

    record_fx_audit(
        db,
        base=base,
        quote=quote,
        rate_date=body.rate_date,
        old_rate=old_rate,
        new_rate=body.rate,
        source=body.source,
    )
    db.commit()
    db.refresh(row)
    return row


def _latest_rate(db: Session, base: str, quote: str, on_date: date | None) -> CambioFxRate | None:
    q = db.query(CambioFxRate).filter(
        CambioFxRate.base_currency == base,
        CambioFxRate.quote_currency == quote,
    )
    if on_date:
        q = q.filter(CambioFxRate.rate_date <= on_date)
    return q.order_by(CambioFxRate.rate_date.desc()).first()


def convert_cents(
    db: Session, amount_cents: int, from_ccy: str, to_ccy: str, on_date: date | None = None
) -> dict:
    from_ccy, to_ccy = from_ccy.upper(), to_ccy.upper()
    if from_ccy == to_ccy:
        return {
            "amount_cents": amount_cents,
            "from_currency": from_ccy,
            "to_currency": to_ccy,
            "to_amount_cents": amount_cents,
            "rate": None,
            "rate_date": on_date,
        }
    direct = _latest_rate(db, from_ccy, to_ccy, on_date)
    if direct:
        rate = Decimal(str(direct.rate))
        converted = int((Decimal(amount_cents) * rate).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        return {
            "amount_cents": amount_cents,
            "from_currency": from_ccy,
            "to_currency": to_ccy,
            "to_amount_cents": converted,
            "rate": rate,
            "rate_date": direct.rate_date,
        }
    inverse = _latest_rate(db, to_ccy, from_ccy, on_date)
    if inverse and Decimal(str(inverse.rate)) != 0:
        rate = (Decimal("1") / Decimal(str(inverse.rate))).quantize(Decimal("0.00000001"))
        converted = int((Decimal(amount_cents) * rate).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        return {
            "amount_cents": amount_cents,
            "from_currency": from_ccy,
            "to_currency": to_ccy,
            "to_amount_cents": converted,
            "rate": rate,
            "rate_date": inverse.rate_date,
        }
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="fx_rate_not_found")
