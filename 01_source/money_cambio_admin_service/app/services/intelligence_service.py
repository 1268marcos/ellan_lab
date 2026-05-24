from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.cambio import CambioFxRate
from app.models.intelligence import (
    MoneyEcosystemInsight,
    MoneyFxAlertEvent,
    MoneyFxAlertRule,
    MoneyPlayerReadiness,
    MoneySettlementSchedule,
)
from app.models.professional import (
    CambioPaymentCorridor,
    MoneyComplianceLimit,
    MoneyLockerPlayerRegistry,
    MoneyOperatingCountry,
    MoneyPlayerRelation,
)
from app.schemas.intelligence import (
    FxAlertRuleIn,
    IntelligenceAnalyzeOut,
    IntelligenceDashboardOut,
    SettlementScheduleIn,
)
from app.services.crypto_util import new_id

STALE_FX_DAYS = 7


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _grade(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 60:
        return "C"
    if score >= 45:
        return "D"
    return "F"


def _upsert_insight(
    db: Session,
    *,
    player_code: str | None,
    corridor_code: str | None,
    insight_type: str,
    severity: str,
    title: str,
    detail: dict,
    suggested_action: str | None,
) -> bool:
    q = db.query(MoneyEcosystemInsight).filter(
        MoneyEcosystemInsight.insight_type == insight_type,
        MoneyEcosystemInsight.title == title,
        MoneyEcosystemInsight.status == "OPEN",
    )
    if player_code:
        q = q.filter(MoneyEcosystemInsight.player_code == player_code)
    if corridor_code:
        q = q.filter(MoneyEcosystemInsight.corridor_code == corridor_code)
    existing = q.first()
    if existing:
        existing.severity = severity
        existing.detail_json = detail
        existing.suggested_action = suggested_action
        existing.detected_at = _utcnow()
        return False
    db.add(
        MoneyEcosystemInsight(
            id=new_id(),
            player_code=player_code,
            corridor_code=corridor_code,
            insight_type=insight_type,
            severity=severity,
            title=title,
            detail_json=detail,
            suggested_action=suggested_action,
            status="OPEN",
        )
    )
    return True


def _relation_count(db: Session, player_code: str) -> int:
    return (
        db.query(MoneyPlayerRelation)
        .filter(
            MoneyPlayerRelation.is_active.is_(True),
            (MoneyPlayerRelation.from_player_code == player_code)
            | (MoneyPlayerRelation.to_player_code == player_code),
        )
        .count()
    )


def _has_fx_for_currency(db: Session, currency: str) -> bool:
    c = currency.upper()
    return (
        db.query(CambioFxRate)
        .filter(
            ((CambioFxRate.base_currency == c) | (CambioFxRate.quote_currency == c)),
            CambioFxRate.rate_date >= date.today() - timedelta(days=STALE_FX_DAYS),
        )
        .first()
        is not None
    )


def _score_player(
    db: Session,
    player: MoneyLockerPlayerRegistry,
    *,
    rel_count: int,
    active_countries: set[str],
) -> MoneyPlayerReadiness:
    fiscal_linked = bool(player.fiscal_corridor_code)
    cambio_linked = bool(player.cambio_corridor_code)
    fx_linked = _has_fx_for_currency(db, player.default_settlement_currency)
    country_ok = player.primary_country in active_countries
    compliance_ok = (
        db.query(MoneyComplianceLimit)
        .filter(
            MoneyComplianceLimit.country_code == player.primary_country,
            MoneyComplianceLimit.is_active.is_(True),
        )
        .first()
        is not None
    )
    corridor_count = 0
    if player.cambio_corridor_code:
        corridor_count = (
            db.query(CambioPaymentCorridor)
            .filter(
                CambioPaymentCorridor.corridor_code == player.cambio_corridor_code,
                CambioPaymentCorridor.is_active.is_(True),
            )
            .count()
        )

    score = 20
    if fiscal_linked:
        score += 20
    if cambio_linked:
        score += 15
    if fx_linked:
        score += 20
    if country_ok:
        score += 10
    if compliance_ok:
        score += 10
    if rel_count >= 1:
        score += min(15, rel_count * 5)
    if corridor_count:
        score += 5
    score = min(100, score)

    return MoneyPlayerReadiness(
        player_code=player.player_code,
        readiness_score=score,
        grade=_grade(score),
        fx_linked=fx_linked,
        fiscal_linked=fiscal_linked,
        compliance_ok=compliance_ok,
        relation_count=rel_count,
        corridor_count=corridor_count,
        detail_json={
            "cambio_linked": cambio_linked,
            "country_registered": country_ok,
            "segment": player.segment,
            "settlement_currency": player.default_settlement_currency,
        },
        computed_at=_utcnow(),
    )


def analyze_ecosystem(db: Session, *, commit: bool = True) -> IntelligenceAnalyzeOut:
    created = updated = 0
    fx_events = 0
    db.flush()

    active_countries = {
        r.country_code
        for r in db.query(MoneyOperatingCountry).filter(MoneyOperatingCountry.is_active.is_(True)).all()
    }
    players = (
        db.query(MoneyLockerPlayerRegistry).filter(MoneyLockerPlayerRegistry.is_active.is_(True)).all()
    )

    for player in players:
        code = player.player_code
        rel_count = _relation_count(db, code)
        readiness = _score_player(db, player, rel_count=rel_count, active_countries=active_countries)
        existing = db.get(MoneyPlayerReadiness, code)
        if existing:
            for k in (
                "readiness_score",
                "grade",
                "fx_linked",
                "fiscal_linked",
                "compliance_ok",
                "relation_count",
                "corridor_count",
                "detail_json",
                "computed_at",
            ):
                setattr(existing, k, getattr(readiness, k))
        else:
            db.add(readiness)

        if not player.fiscal_corridor_code:
            if _upsert_insight(
                db,
                player_code=code,
                corridor_code=None,
                insight_type="MISSING_FISCAL_LINK",
                severity="HIGH",
                title=f"{code}: sem corredor fiscal",
                detail={"player_code": code, "segment": player.segment},
                suggested_action="Definir fiscal_corridor_code ou sync Finance + catálogo Money.",
            ):
                created += 1
            else:
                updated += 1

        if not player.cambio_corridor_code:
            if _upsert_insight(
                db,
                player_code=code,
                corridor_code=None,
                insight_type="MISSING_CAMBIO_CORRIDOR",
                severity="MEDIUM",
                title=f"{code}: sem corredor cambio",
                detail={"player_code": code},
                suggested_action="Criar corredor em cambio_payment_corridor ou alinhar seed.",
            ):
                created += 1
            else:
                updated += 1

        if not readiness.fx_linked:
            if _upsert_insight(
                db,
                player_code=code,
                corridor_code=None,
                insight_type="STALE_OR_MISSING_FX",
                severity="HIGH",
                title=f"{code}: FX ausente para {player.default_settlement_currency}",
                detail={"currency": player.default_settlement_currency},
                suggested_action="POST /fx-rates ou integrar parceiro FX_FEED.",
            ):
                created += 1
            else:
                updated += 1

        if rel_count == 0 and player.segment in (
            "MARKETPLACE",
            "LOGISTICS_PLATFORM",
            "COLLECTION_POINT",
        ):
            if _upsert_insight(
                db,
                player_code=code,
                corridor_code=None,
                insight_type="ISOLATED_PLAYER",
                severity="LOW",
                title=f"{code}: sem relações no ecossistema",
                detail={"segment": player.segment},
                suggested_action="Adicionar PLAYER_RELATIONS (carrier, white-label, agregador).",
            ):
                created += 1
            else:
                updated += 1

    for corridor in db.query(CambioPaymentCorridor).filter(CambioPaymentCorridor.is_active.is_(True)).all():
        pair = f"{corridor.transaction_currency}/{corridor.settlement_currency}"
        if corridor.transaction_currency == corridor.settlement_currency:
            continue
        has_rate = (
            db.query(CambioFxRate)
            .filter(
                CambioFxRate.base_currency == corridor.transaction_currency,
                CambioFxRate.quote_currency == corridor.settlement_currency,
            )
            .first()
        )
        if not has_rate:
            if _upsert_insight(
                db,
                player_code=None,
                corridor_code=corridor.corridor_code,
                insight_type="CORRIDOR_NO_FX",
                severity="HIGH",
                title=f"Corredor {corridor.corridor_code} sem taxa {pair}",
                detail={"corridor_code": corridor.corridor_code, "pair": pair},
                suggested_action="Cadastrar taxa FX para o par do corredor.",
            ):
                created += 1
            else:
                updated += 1

    fx_events = evaluate_fx_alerts(db)

    scores = [r.readiness_score for r in db.query(MoneyPlayerReadiness).all()]
    avg = round(sum(scores) / len(scores), 1) if scores else 0.0
    if commit:
        db.commit()
    return IntelligenceAnalyzeOut(
        players_scored=len(players),
        insights_created=created,
        insights_updated=updated,
        fx_events_triggered=fx_events,
        avg_readiness=avg,
    )


def evaluate_fx_alerts(db: Session) -> int:
    triggered = 0
    rules = db.query(MoneyFxAlertRule).filter(MoneyFxAlertRule.is_active.is_(True)).all()
    for rule in rules:
        rates = (
            db.query(CambioFxRate)
            .filter(
                CambioFxRate.base_currency == rule.base_currency.upper(),
                CambioFxRate.quote_currency == rule.quote_currency.upper(),
            )
            .order_by(CambioFxRate.rate_date.desc())
            .limit(2)
            .all()
        )
        if len(rates) < 2:
            continue
        current, previous = rates[0], rates[1]
        if not previous.rate or previous.rate == 0:
            continue
        change = float(current.rate) - float(previous.rate)
        change_bps = int(abs(change / float(previous.rate)) * 10000)
        if change_bps < rule.threshold_bps:
            continue
        if rule.direction == "UP" and change <= 0:
            continue
        if rule.direction == "DOWN" and change >= 0:
            continue
        db.add(
            MoneyFxAlertEvent(
                id=new_id(),
                rule_id=rule.id,
                base_currency=rule.base_currency.upper(),
                quote_currency=rule.quote_currency.upper(),
                previous_rate=previous.rate,
                current_rate=current.rate,
                change_bps=change_bps,
                status="OPEN",
            )
        )
        triggered += 1
    return triggered


def intelligence_dashboard(db: Session) -> IntelligenceDashboardOut:
    players_total = (
        db.query(func.count(MoneyLockerPlayerRegistry.id))
        .filter(MoneyLockerPlayerRegistry.is_active.is_(True))
        .scalar()
        or 0
    )
    readiness_rows = db.query(MoneyPlayerReadiness).all()
    avg = (
        round(sum(r.readiness_score for r in readiness_rows) / len(readiness_rows), 1)
        if readiness_rows
        else 0.0
    )
    grade_dist: dict[str, int] = {}
    for r in readiness_rows:
        grade_dist[r.grade] = grade_dist.get(r.grade, 0) + 1

    open_insights = (
        db.query(func.count(MoneyEcosystemInsight.id))
        .filter(MoneyEcosystemInsight.status == "OPEN")
        .scalar()
        or 0
    )
    sev_rows = (
        db.query(MoneyEcosystemInsight.severity, func.count(MoneyEcosystemInsight.id))
        .filter(MoneyEcosystemInsight.status == "OPEN")
        .group_by(MoneyEcosystemInsight.severity)
        .all()
    )
    by_sev = {s: int(c) for s, c in sev_rows}

    open_fx = (
        db.query(func.count(MoneyFxAlertEvent.id))
        .filter(MoneyFxAlertEvent.status == "OPEN")
        .scalar()
        or 0
    )

    top = (
        db.query(MoneyEcosystemInsight.title)
        .filter(MoneyEcosystemInsight.status == "OPEN", MoneyEcosystemInsight.severity == "HIGH")
        .order_by(MoneyEcosystemInsight.detected_at.desc())
        .limit(5)
        .all()
    )

    return IntelligenceDashboardOut(
        players_total=players_total,
        avg_readiness=avg,
        grade_distribution=grade_dist,
        open_insights=open_insights,
        insights_by_severity=by_sev,
        open_fx_alerts=open_fx,
        settlement_schedules=db.query(func.count(MoneySettlementSchedule.id)).scalar() or 0,
        corridors_active=db.query(func.count(CambioPaymentCorridor.id))
        .filter(CambioPaymentCorridor.is_active.is_(True))
        .scalar()
        or 0,
        fx_rates_count=db.query(func.count(CambioFxRate.id)).scalar() or 0,
        top_gaps=[t[0] for t in top],
    )


def list_readiness(db: Session, *, min_score: int | None = None, grade: str | None = None) -> list[MoneyPlayerReadiness]:
    q = db.query(MoneyPlayerReadiness)
    if min_score is not None:
        q = q.filter(MoneyPlayerReadiness.readiness_score >= min_score)
    if grade:
        q = q.filter(MoneyPlayerReadiness.grade == grade.upper())
    return q.order_by(MoneyPlayerReadiness.readiness_score.desc()).all()


def list_insights(
    db: Session,
    *,
    status: str | None = "OPEN",
    severity: str | None = None,
    player_code: str | None = None,
    limit: int = 100,
) -> list[MoneyEcosystemInsight]:
    q = db.query(MoneyEcosystemInsight)
    if status:
        q = q.filter(MoneyEcosystemInsight.status == status.upper())
    if severity:
        q = q.filter(MoneyEcosystemInsight.severity == severity.upper())
    if player_code:
        q = q.filter(MoneyEcosystemInsight.player_code == player_code.upper())
    return q.order_by(MoneyEcosystemInsight.detected_at.desc()).limit(limit).all()


def resolve_insight(db: Session, insight_id: str) -> MoneyEcosystemInsight:
    row = db.get(MoneyEcosystemInsight, insight_id)
    if not row:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="insight_not_found")
    row.status = "RESOLVED"
    row.resolved_at = _utcnow()
    db.commit()
    db.refresh(row)
    return row


def list_fx_rules(db: Session) -> list[MoneyFxAlertRule]:
    return db.query(MoneyFxAlertRule).order_by(MoneyFxAlertRule.name).all()


def create_fx_rule(db: Session, body: FxAlertRuleIn) -> MoneyFxAlertRule:
    row = MoneyFxAlertRule(
        id=new_id(),
        name=body.name,
        base_currency=body.base_currency.upper(),
        quote_currency=body.quote_currency.upper(),
        threshold_bps=body.threshold_bps,
        direction=body.direction.upper(),
        is_active=body.is_active,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_fx_events(db: Session, *, status: str | None = "OPEN") -> list[MoneyFxAlertEvent]:
    q = db.query(MoneyFxAlertEvent)
    if status:
        q = q.filter(MoneyFxAlertEvent.status == status.upper())
    return q.order_by(MoneyFxAlertEvent.triggered_at.desc()).limit(50).all()


def acknowledge_fx_event(db: Session, event_id: str) -> MoneyFxAlertEvent:
    row = db.get(MoneyFxAlertEvent, event_id)
    if not row:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="event_not_found")
    row.status = "ACK"
    row.acknowledged_at = _utcnow()
    db.commit()
    db.refresh(row)
    return row


def list_settlement_schedules(
    db: Session, *, scope_code: str | None = None
) -> list[MoneySettlementSchedule]:
    q = db.query(MoneySettlementSchedule).filter(MoneySettlementSchedule.is_active.is_(True))
    if scope_code:
        q = q.filter(MoneySettlementSchedule.scope_code == scope_code.upper())
    return q.order_by(MoneySettlementSchedule.scope_code, MoneySettlementSchedule.country_code).all()


def create_settlement_schedule(db: Session, body: SettlementScheduleIn) -> MoneySettlementSchedule:
    row = MoneySettlementSchedule(
        id=new_id(),
        scope_type=body.scope_type.upper(),
        scope_code=body.scope_code.upper(),
        country_code=body.country_code.upper(),
        settlement_currency=body.settlement_currency.upper(),
        settlement_days=body.settlement_days,
        cut_off_time_utc=body.cut_off_time_utc,
        weekend_policy=body.weekend_policy,
        notes=body.notes,
        is_active=body.is_active,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def seed_intelligence_defaults(db: Session) -> dict[str, int]:
    counts = {"fx_rules": 0, "settlements": 0}
    defaults_rules = [
        ("USD/BRL volatilidade", "USD", "BRL", 150, "BOTH"),
        ("EUR/BRL volatilidade", "EUR", "BRL", 120, "BOTH"),
        ("EUR/USD cross", "EUR", "USD", 80, "BOTH"),
    ]
    for name, base, quote, bps, direction in defaults_rules:
        exists = (
            db.query(MoneyFxAlertRule)
            .filter(
                MoneyFxAlertRule.base_currency == base,
                MoneyFxAlertRule.quote_currency == quote,
            )
            .first()
        )
        if not exists:
            db.add(
                MoneyFxAlertRule(
                    id=new_id(),
                    name=name,
                    base_currency=base,
                    quote_currency=quote,
                    threshold_bps=bps,
                    direction=direction,
                    is_active=True,
                )
            )
            counts["fx_rules"] += 1

    settlements = [
        ("PLAYER", "MAGALU", "BR", "BRL", 1, "18:00"),
        ("PLAYER", "INPOST", "PL", "PLN", 2, "16:00"),
        ("PLAYER", "CORREIOS", "BR", "BRL", 3, "14:00"),
        ("CORRIDOR", "BR-PT-CROSSBORDER", "BR", "BRL", 5, "15:00"),
        ("CORRIDOR", "PL-EU-INPOST-LOCKER", "PL", "PLN", 2, "17:00"),
    ]
    for scope_type, scope_code, country, ccy, days, cut in settlements:
        exists = (
            db.query(MoneySettlementSchedule)
            .filter(
                MoneySettlementSchedule.scope_type == scope_type,
                MoneySettlementSchedule.scope_code == scope_code,
                MoneySettlementSchedule.country_code == country,
            )
            .first()
        )
        if not exists:
            db.add(
                MoneySettlementSchedule(
                    id=new_id(),
                    scope_type=scope_type,
                    scope_code=scope_code,
                    country_code=country,
                    settlement_currency=ccy,
                    settlement_days=days,
                    cut_off_time_utc=cut,
                    is_active=True,
                )
            )
            counts["settlements"] += 1
    return counts
