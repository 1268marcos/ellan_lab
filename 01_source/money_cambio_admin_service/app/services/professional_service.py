from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.catalog import PaymentMethodCatalog, WalletProviderCatalog
from app.models.cambio import CambioFxRate
from app.models.integration import MoneyCambioIntegrationPartner
from app.models.money import MoneyCurrencyCatalog
from app.data.global_locker_money_catalog import (
    ALL_MONEY_PLAYERS,
    COUNTRY_LOCKER_NETWORKS,
    FISCAL_ALIGNED_CORRIDORS,
)
from app.data.global_locker_money_catalog_world import (
    MONEY_ECOSYSTEM_SEGMENTS,
    MONEY_PLAYER_RELATIONS,
)
from app.models.intelligence import MoneyEcosystemInsight, MoneyFxAlertEvent, MoneyPlayerReadiness
from app.models.professional import (
    CambioCorridorMarkup,
    CambioFxRateAudit,
    CambioPaymentCorridor,
    MoneyComplianceLimit,
    MoneyEcosystemSegment,
    MoneyLockerPlayerRegistry,
    MoneyMethodCountryMatrix,
    MoneyOperatingCountry,
    MoneyPlayerRelation,
    MoneyWalletCountryMatrix,
)
from app.schemas.professional import (
    ComplianceLimitIn,
    CorridorMarkupIn,
    GlobalOpsDashboardOut,
    MethodCountryMatrixIn,
    OperatingCountryIn,
    OperatingCountryUpdate,
    PaymentCorridorIn,
    PaymentCorridorUpdate,
    WalletCountryMatrixIn,
)
from app.services.crypto_util import new_id

WORLD_COUNTRY_TARGET = 24


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# --- operating countries ---


def list_countries(db: Session, active_only: bool = False, zone: str | None = None) -> list[MoneyOperatingCountry]:
    q = db.query(MoneyOperatingCountry)
    if active_only:
        q = q.filter(MoneyOperatingCountry.is_active.is_(True))
    if zone:
        q = q.filter(MoneyOperatingCountry.regulatory_zone == zone.upper())
    return q.order_by(MoneyOperatingCountry.country_code).all()


def create_country(db: Session, body: OperatingCountryIn) -> MoneyOperatingCountry:
    cc = body.country_code.upper()
    if db.query(MoneyOperatingCountry).filter(MoneyOperatingCountry.country_code == cc).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="country_code_exists")
    row = MoneyOperatingCountry(
        country_code=cc,
        default_currency_code=body.default_currency_code.upper(),
        **body.model_dump(exclude={"country_code", "default_currency_code"}),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_country(db: Session, country_code: str, body: OperatingCountryUpdate) -> MoneyOperatingCountry:
    row = db.query(MoneyOperatingCountry).filter(MoneyOperatingCountry.country_code == country_code.upper()).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="country_not_found")
    for k, v in body.model_dump(exclude_unset=True).items():
        if k == "default_currency_code" and v:
            setattr(row, k, v.upper())
        else:
            setattr(row, k, v)
    row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    return row


# --- method country matrix ---


def list_method_matrix(
    db: Session, country_code: str | None = None, active_only: bool = False
) -> list[MoneyMethodCountryMatrix]:
    q = db.query(MoneyMethodCountryMatrix)
    if country_code:
        q = q.filter(MoneyMethodCountryMatrix.country_code == country_code.upper())
    if active_only:
        q = q.filter(MoneyMethodCountryMatrix.is_active.is_(True))
    return q.order_by(MoneyMethodCountryMatrix.country_code, MoneyMethodCountryMatrix.sort_order).all()


def create_method_matrix(db: Session, body: MethodCountryMatrixIn) -> MoneyMethodCountryMatrix:
    cc = body.country_code.upper()
    exists = (
        db.query(MoneyMethodCountryMatrix)
        .filter(
            MoneyMethodCountryMatrix.country_code == cc,
            MoneyMethodCountryMatrix.payment_method_code == body.payment_method_code,
        )
        .first()
    )
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="matrix_row_exists")
    row = MoneyMethodCountryMatrix(country_code=cc, **body.model_dump(exclude={"country_code"}))
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def delete_method_matrix(db: Session, row_id: int) -> None:
    row = db.get(MoneyMethodCountryMatrix, row_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="matrix_row_not_found")
    db.delete(row)
    db.commit()


# --- wallet country matrix ---


def list_wallet_matrix(db: Session, country_code: str | None = None) -> list[MoneyWalletCountryMatrix]:
    q = db.query(MoneyWalletCountryMatrix)
    if country_code:
        q = q.filter(MoneyWalletCountryMatrix.country_code == country_code.upper())
    return q.order_by(MoneyWalletCountryMatrix.country_code).all()


def create_wallet_matrix(db: Session, body: WalletCountryMatrixIn) -> MoneyWalletCountryMatrix:
    cc = body.country_code.upper()
    exists = (
        db.query(MoneyWalletCountryMatrix)
        .filter(
            MoneyWalletCountryMatrix.country_code == cc,
            MoneyWalletCountryMatrix.wallet_provider_code == body.wallet_provider_code,
        )
        .first()
    )
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="wallet_matrix_exists")
    row = MoneyWalletCountryMatrix(country_code=cc, **body.model_dump(exclude={"country_code"}))
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


# --- payment corridors ---


def list_corridors(
    db: Session, origin: str | None = None, destination: str | None = None, active_only: bool = False
) -> list[CambioPaymentCorridor]:
    q = db.query(CambioPaymentCorridor)
    if origin:
        q = q.filter(CambioPaymentCorridor.origin_country_code == origin.upper())
    if destination:
        q = q.filter(CambioPaymentCorridor.destination_country_code == destination.upper())
    if active_only:
        q = q.filter(CambioPaymentCorridor.is_active.is_(True))
    return q.order_by(CambioPaymentCorridor.corridor_code).all()


def create_corridor(db: Session, body: PaymentCorridorIn) -> CambioPaymentCorridor:
    if db.query(CambioPaymentCorridor).filter(CambioPaymentCorridor.corridor_code == body.corridor_code).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="corridor_code_exists")
    pid = body.id or new_id()
    data = body.model_dump(exclude={"id"})
    data["origin_country_code"] = data["origin_country_code"].upper()
    data["destination_country_code"] = data["destination_country_code"].upper()
    data["transaction_currency"] = data["transaction_currency"].upper()
    data["settlement_currency"] = data["settlement_currency"].upper()
    row = CambioPaymentCorridor(id=pid, **data)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_corridor(db: Session, corridor_id: str, body: PaymentCorridorUpdate) -> CambioPaymentCorridor:
    row = db.get(CambioPaymentCorridor, corridor_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="corridor_not_found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    return row


def list_corridor_markups(db: Session, corridor_id: str | None = None) -> list[CambioCorridorMarkup]:
    q = db.query(CambioCorridorMarkup)
    if corridor_id:
        q = q.filter(CambioCorridorMarkup.corridor_id == corridor_id)
    return q.order_by(CambioCorridorMarkup.valid_from.desc()).all()


def create_corridor_markup(db: Session, body: CorridorMarkupIn) -> CambioCorridorMarkup:
    if not db.get(CambioPaymentCorridor, body.corridor_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="corridor_not_found")
    row = CambioCorridorMarkup(id=new_id(), **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


# --- compliance ---


def list_compliance(db: Session, country_code: str | None = None) -> list[MoneyComplianceLimit]:
    q = db.query(MoneyComplianceLimit)
    if country_code:
        q = q.filter(MoneyComplianceLimit.country_code == country_code.upper())
    return q.order_by(MoneyComplianceLimit.country_code, MoneyComplianceLimit.limit_type).all()


def create_compliance(db: Session, body: ComplianceLimitIn) -> MoneyComplianceLimit:
    row = MoneyComplianceLimit(
        id=new_id(),
        country_code=body.country_code.upper(),
        currency_code=body.currency_code.upper(),
        **body.model_dump(exclude={"country_code", "currency_code"}),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_fx_audit(db: Session, limit: int = 50) -> list[CambioFxRateAudit]:
    return db.query(CambioFxRateAudit).order_by(CambioFxRateAudit.created_at.desc()).limit(limit).all()


def record_fx_audit(
    db: Session,
    *,
    base: str,
    quote: str,
    rate_date,
    old_rate,
    new_rate,
    source: str,
    changed_by: str = "system",
) -> None:
    db.add(
        CambioFxRateAudit(
            id=new_id(),
            base_currency=base,
            quote_currency=quote,
            rate_date=rate_date,
            old_rate=old_rate,
            new_rate=new_rate,
            source=source,
            changed_by=changed_by,
        )
    )


def list_locker_players(
    db: Session, segment: str | None = None, active_only: bool = True
) -> list[MoneyLockerPlayerRegistry]:
    q = db.query(MoneyLockerPlayerRegistry)
    if segment:
        q = q.filter(MoneyLockerPlayerRegistry.segment == segment.upper())
    if active_only:
        q = q.filter(MoneyLockerPlayerRegistry.is_active.is_(True))
    return q.order_by(MoneyLockerPlayerRegistry.segment, MoneyLockerPlayerRegistry.player_code).all()


def ecosystem_matrix(db: Session) -> list[dict]:
    rows = list_locker_players(db, active_only=True)
    out = []
    for r in rows:
        fin = r.finance_catalog_code or r.player_code
        fis = r.fiscal_corridor_code or "—"
        out.append(
            {
                "player_code": r.player_code,
                "name": r.name,
                "finance_catalog_code": r.finance_catalog_code,
                "fiscal_corridor_code": r.fiscal_corridor_code,
                "cambio_corridor_code": r.cambio_corridor_code,
                "finance_admin_path": f"/ops/finance/admin (catalog: {fin})",
                "fiscal_admin_path": f"/ops/fiscal/admin?tab=corridors ({fis})",
            }
        )
    return out


def list_ecosystem_segments(db: Session, active_only: bool = True) -> list[dict]:
    segments = db.query(MoneyEcosystemSegment)
    if active_only:
        segments = segments.filter(MoneyEcosystemSegment.is_active.is_(True))
    rows = segments.order_by(MoneyEcosystemSegment.sort_order).all()
    counts: dict[str, int] = {}
    for seg, n in (
        db.query(MoneyLockerPlayerRegistry.segment, func.count(MoneyLockerPlayerRegistry.id))
        .filter(MoneyLockerPlayerRegistry.is_active.is_(True))
        .group_by(MoneyLockerPlayerRegistry.segment)
        .all()
    ):
        counts[seg] = int(n)
    return [
        {
            "code": r.code,
            "name": r.name,
            "description": r.description,
            "sort_order": r.sort_order,
            "is_active": r.is_active,
            "player_count": counts.get(r.code, 0),
        }
        for r in rows
    ]


def list_player_relations(
    db: Session,
    *,
    from_player: str | None = None,
    to_player: str | None = None,
    relation_type: str | None = None,
    active_only: bool = True,
) -> list[MoneyPlayerRelation]:
    q = db.query(MoneyPlayerRelation)
    if from_player:
        q = q.filter(MoneyPlayerRelation.from_player_code == from_player.upper())
    if to_player:
        q = q.filter(MoneyPlayerRelation.to_player_code == to_player.upper())
    if relation_type:
        q = q.filter(MoneyPlayerRelation.relation_type == relation_type.upper())
    if active_only:
        q = q.filter(MoneyPlayerRelation.is_active.is_(True))
    return q.order_by(
        MoneyPlayerRelation.relation_type,
        MoneyPlayerRelation.from_player_code,
        MoneyPlayerRelation.to_player_code,
    ).all()


def ecosystem_intelligence(db: Session) -> dict:
    segments = list_ecosystem_segments(db)
    by_segment = {s["code"]: s["player_count"] for s in segments}
    players_total = db.query(func.count(MoneyLockerPlayerRegistry.id)).scalar() or 0
    relations_total = db.query(func.count(MoneyPlayerRelation.id)).scalar() or 0
    return {
        "segments": segments,
        "relations_total": relations_total,
        "players_total": players_total,
        "by_segment": by_segment,
        "integration_modes": [
            "REST",
            "WEBHOOK",
            "AGGREGATOR",
            "WHITE_LABEL",
            "CHANNEL_USES_CARRIER",
            "OPERATES_NETWORK",
        ],
    }


def seed_ecosystem_world(db: Session) -> dict[str, int]:
    counts = {"segments": 0, "relations": 0}
    for spec in MONEY_ECOSYSTEM_SEGMENTS:
        code = spec["code"]
        row = db.query(MoneyEcosystemSegment).filter(MoneyEcosystemSegment.code == code).first()
        if row:
            row.name = spec["name"]
            row.description = spec.get("description")
            row.sort_order = spec.get("sort_order", 100)
            row.is_active = True
        else:
            db.add(
                MoneyEcosystemSegment(
                    code=code,
                    name=spec["name"],
                    description=spec.get("description"),
                    sort_order=spec.get("sort_order", 100),
                    is_active=True,
                )
            )
            counts["segments"] += 1

    for rel in MONEY_PLAYER_RELATIONS:
        exists = (
            db.query(MoneyPlayerRelation)
            .filter(
                MoneyPlayerRelation.from_player_code == rel["from"],
                MoneyPlayerRelation.to_player_code == rel["to"],
                MoneyPlayerRelation.relation_type == rel["type"],
            )
            .first()
        )
        if exists:
            continue
        db.add(
            MoneyPlayerRelation(
                id=new_id(),
                from_player_code=rel["from"],
                to_player_code=rel["to"],
                relation_type=rel["type"],
                notes=rel.get("notes"),
                metadata_json={"source": "global_locker_money_catalog_world"},
                is_active=True,
            )
        )
        counts["relations"] += 1
    return counts


def seed_locker_players(db: Session) -> dict[str, int]:
    counts = {"players": 0, "corridors": 0, "countries_updated": 0, "segments": 0, "relations": 0}
    eco = seed_ecosystem_world(db)
    counts["segments"] = eco["segments"]
    counts["relations"] = eco["relations"]

    for spec in ALL_MONEY_PLAYERS:
        code = spec["player_code"]
        if db.query(MoneyLockerPlayerRegistry).filter(MoneyLockerPlayerRegistry.player_code == code).first():
            continue
        db.add(
            MoneyLockerPlayerRegistry(
                id=new_id(),
                player_code=code,
                name=spec["name"],
                segment=spec["segment"],
                primary_country=spec["primary_country"],
                regions_json=spec.get("regions") or [],
                default_settlement_currency=spec["default_settlement_currency"],
                finance_catalog_code=spec.get("finance_catalog_code"),
                fiscal_corridor_code=spec.get("fiscal_corridor_code"),
                cambio_corridor_code=spec.get("cambio_corridor_code"),
                notes=spec.get("notes"),
                metadata_json={"source": "global_locker_money_catalog"},
                is_active=True,
            )
        )
        counts["players"] += 1

    for cc, networks in COUNTRY_LOCKER_NETWORKS.items():
        row = db.query(MoneyOperatingCountry).filter(MoneyOperatingCountry.country_code == cc).first()
        if row:
            row.locker_networks_json = networks
            row.updated_at = _utcnow()
            counts["countries_updated"] += 1

    for code, name, orig, dest, tx, settle, ctype, spread, partner in FISCAL_ALIGNED_CORRIDORS:
        if db.query(CambioPaymentCorridor).filter(CambioPaymentCorridor.corridor_code == code).first():
            continue
        db.add(
            CambioPaymentCorridor(
                id=new_id(),
                corridor_code=code,
                name=name,
                origin_country_code=orig,
                destination_country_code=dest,
                transaction_currency=tx,
                settlement_currency=settle,
                corridor_type=ctype,
                default_spread_bps=spread,
                fx_partner_code=partner,
                notes=f"Alinhado fiscal_tax_corridors / finance_locker_network_catalog",
                is_active=True,
            )
        )
        counts["corridors"] += 1

    return counts


def global_dashboard(db: Session) -> GlobalOpsDashboardOut:
    countries = db.query(func.count(MoneyOperatingCountry.id)).scalar() or 0
    active_countries = (
        db.query(func.count(MoneyOperatingCountry.id)).filter(MoneyOperatingCountry.is_active.is_(True)).scalar() or 0
    )
    coverage = min(100.0, round(100.0 * active_countries / WORLD_COUNTRY_TARGET, 1))
    grade = "A" if coverage >= 90 else "B" if coverage >= 70 else "C" if coverage >= 50 else "D"
    return GlobalOpsDashboardOut(
        currencies=db.query(func.count(MoneyCurrencyCatalog.id)).scalar() or 0,
        countries=countries,
        payment_methods=db.query(func.count(PaymentMethodCatalog.id)).scalar() or 0,
        wallets=db.query(func.count(WalletProviderCatalog.id)).scalar() or 0,
        corridors=db.query(func.count(CambioPaymentCorridor.id)).scalar() or 0,
        fx_rates=db.query(func.count(CambioFxRate.id)).scalar() or 0,
        method_matrix_rows=db.query(func.count(MoneyMethodCountryMatrix.id)).scalar() or 0,
        compliance_limits=db.query(func.count(MoneyComplianceLimit.id)).scalar() or 0,
        integration_partners=db.query(func.count(MoneyCambioIntegrationPartner.id)).scalar() or 0,
        locker_players=db.query(func.count(MoneyLockerPlayerRegistry.id)).scalar() or 0,
        ecosystem_segments=db.query(func.count(MoneyEcosystemSegment.code)).scalar() or 0,
        player_relations=db.query(func.count(MoneyPlayerRelation.id)).scalar() or 0,
        avg_player_readiness=round(
            float(
                db.query(func.avg(MoneyPlayerReadiness.readiness_score)).scalar() or 0
            ),
            1,
        ),
        open_insights=db.query(func.count(MoneyEcosystemInsight.id))
        .filter(MoneyEcosystemInsight.status == "OPEN")
        .scalar()
        or 0,
        open_fx_alerts=db.query(func.count(MoneyFxAlertEvent.id))
        .filter(MoneyFxAlertEvent.status == "OPEN")
        .scalar()
        or 0,
        world_coverage_pct=coverage,
        readiness_grade=grade,
    )
