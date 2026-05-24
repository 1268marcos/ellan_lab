from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.advanced import MoneyFxLock
from app.models.cambio import CambioFxRate
from app.models.professional import CambioPaymentCorridor, MoneyLockerPlayerRegistry
from app.schemas.advanced import TreasuryDashboardOut, TreasuryExposureRow


def treasury_dashboard(db: Session) -> TreasuryDashboardOut:
    players = (
        db.query(MoneyLockerPlayerRegistry)
        .filter(MoneyLockerPlayerRegistry.is_active.is_(True))
        .all()
    )
    corridors = (
        db.query(CambioPaymentCorridor)
        .filter(CambioPaymentCorridor.is_active.is_(True))
        .all()
    )

    by_ccy: dict[str, dict] = {}
    for p in players:
        c = p.default_settlement_currency
        by_ccy.setdefault(c, {"players": 0, "corridors": set()})
        by_ccy[c]["players"] += 1

    for c in corridors:
        for ccy in (c.transaction_currency, c.settlement_currency):
            by_ccy.setdefault(ccy, {"players": 0, "corridors": set()})
            by_ccy[ccy]["corridors"].add(c.corridor_code)

    fx_pairs = {
        (r.base_currency, r.quote_currency)
        for r in db.query(CambioFxRate.base_currency, CambioFxRate.quote_currency).distinct().all()
    }

    active_locks = (
        db.query(MoneyFxLock.quote_currency, func.count(MoneyFxLock.id))
        .filter(MoneyFxLock.status == "ACTIVE")
        .group_by(MoneyFxLock.quote_currency)
        .all()
    )
    locks_by_ccy = {ccy: int(n) for ccy, n in active_locks}

    exposures: list[TreasuryExposureRow] = []
    gaps: list[str] = []
    for ccy, data in sorted(by_ccy.items()):
        has_fx = any(ccy in pair for pair in fx_pairs)
        if not has_fx and data["players"] >= 3:
            gaps.append(f"Sem par FX configurado para {ccy} ({data['players']} players)")
        risk = "LOW"
        if not has_fx:
            risk = "HIGH"
        elif locks_by_ccy.get(ccy, 0) == 0 and len(data["corridors"]) > 2:
            risk = "MEDIUM"
        exposures.append(
            TreasuryExposureRow(
                currency_code=ccy,
                player_count=data["players"],
                corridor_count=len(data["corridors"]),
                has_fx_rate=has_fx,
                active_locks=locks_by_ccy.get(ccy, 0),
                risk_hint=risk,
            )
        )

    return TreasuryDashboardOut(
        currencies_tracked=len(by_ccy),
        players_active=len(players),
        corridors_active=len(corridors),
        fx_pairs_configured=len(fx_pairs),
        active_fx_locks=sum(locks_by_ccy.values()),
        exposures=exposures,
        gaps=gaps[:10],
    )
