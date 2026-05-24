from __future__ import annotations

import fnmatch
import json
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.fiscal_core import FiscalReconciliationGap
from app.models.fiscal_global import (
    FiscalAutoClassificationRule,
    FiscalComplianceCertification,
    FiscalCorridorTaxRule,
    FiscalIntegrationReadiness,
    FiscalTaxCorridor,
    FiscalWebhookDeliveryLog,
)
from app.models.fiscal_intelligence import FiscalContingencyEvent, FiscalOpsInsight
from app.services.crypto_util import new_id


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def cert_expiry_severity(expires_at: date | None, *, within_days: int = 90) -> str:
    if expires_at is None:
        return "UNKNOWN"
    today = date.today()
    if expires_at < today:
        return "EXPIRED"
    if expires_at <= today + timedelta(days=within_days):
        return "EXPIRING"
    return "VALID"


def _upsert_insight(
    db: Session,
    *,
    entity_type: str,
    entity_ref: str,
    insight_type: str,
    severity: str,
    title: str,
    detail: dict,
    suggested_action: str | None,
) -> bool:
    existing = (
        db.query(FiscalOpsInsight)
        .filter(
            FiscalOpsInsight.entity_type == entity_type,
            FiscalOpsInsight.entity_ref == entity_ref,
            FiscalOpsInsight.insight_type == insight_type,
            FiscalOpsInsight.title == title,
        )
        .first()
    )
    detail_json = json.dumps(detail)
    if existing:
        existing.severity = severity
        existing.detail_json = detail_json
        existing.suggested_action = suggested_action
        if existing.status != "RESOLVED":
            existing.status = "OPEN"
        existing.detected_at = _utcnow()
        return False
    db.add(
        FiscalOpsInsight(
            id=new_id(),
            entity_type=entity_type,
            entity_ref=entity_ref,
            insight_type=insight_type,
            severity=severity,
            title=title,
            detail_json=detail_json,
            suggested_action=suggested_action,
            status="OPEN",
        )
    )
    return True


def analyze_fiscal_ops(db: Session) -> dict[str, int]:
    created = 0
    today = date.today()
    horizon = today + timedelta(days=90)

    for cert in db.query(FiscalComplianceCertification).all():
        if cert.expires_at and cert.expires_at <= horizon:
            sev = "CRITICAL" if cert.expires_at < today else "HIGH" if cert.expires_at <= today + timedelta(days=30) else "MEDIUM"
            if _upsert_insight(
                db,
                entity_type="issuer",
                entity_ref=cert.issuer_code,
                insight_type="cert_expiring",
                severity=sev,
                title=f"Certificação {cert.certification_type} expira em {cert.expires_at.isoformat()}",
                detail={
                    "certification_type": cert.certification_type,
                    "expires_at": cert.expires_at.isoformat(),
                    "issuer_code": cert.issuer_code,
                    "days_left": (cert.expires_at - today).days,
                },
                suggested_action="Renovar certificado A1/homologação antes do vencimento; bloquear emissão se EXPIRED.",
            ):
                created += 1

    dlq_count = (
        db.query(FiscalWebhookDeliveryLog)
        .filter(FiscalWebhookDeliveryLog.delivery_status.in_(["FAILED", "DLQ"]))
        .count()
    )
    if dlq_count > 0:
        if _upsert_insight(
            db,
            entity_type="platform",
            entity_ref="webhook-dlq",
            insight_type="webhook_dlq_backlog",
            severity="HIGH" if dlq_count >= 5 else "MEDIUM",
            title=f"{dlq_count} entrega(s) webhook em DLQ",
            detail={"failed_count": dlq_count},
            suggested_action="Revisar aba Webhooks DLQ e usar Retry; verificar URL e secret do emissor.",
        ):
            created += 1

    for row in db.query(FiscalIntegrationReadiness).filter(FiscalIntegrationReadiness.readiness_band.in_(["C", "D"])).all():
        blockers = json.loads(row.blockers_json or "[]")
        if _upsert_insight(
            db,
            entity_type="issuer",
            entity_ref=row.issuer_code,
            insight_type="readiness_low",
            severity="HIGH" if row.readiness_band == "D" else "MEDIUM",
            title=f"Readiness band {row.readiness_band} (score {row.score_total})",
            detail={"band": row.readiness_band, "score_total": float(row.score_total), "blockers": blockers},
            suggested_action="Completar certificações, api_base_url e plano de contingência.",
        ):
            created += 1

    for corridor in db.query(FiscalTaxCorridor).filter(FiscalTaxCorridor.active.is_(True)).all():
        if not corridor.fallback_issuer_code and corridor.origin_country != corridor.dest_country:
            if _upsert_insight(
                db,
                entity_type="corridor",
                entity_ref=corridor.corridor_code,
                insight_type="corridor_no_fallback",
                severity="MEDIUM",
                title="Corredor cross-border sem emissor fallback",
                detail={
                    "corridor_code": corridor.corridor_code,
                    "origin": corridor.origin_country,
                    "dest": corridor.dest_country,
                },
                suggested_action="Cadastrar emissor fallback para contingência cross-border.",
            ):
                created += 1

    for gap in (
        db.query(FiscalReconciliationGap)
        .filter(FiscalReconciliationGap.status == "OPEN", FiscalReconciliationGap.severity == "HIGH")
        .all()
    ):
        if _upsert_insight(
            db,
            entity_type="gap",
            entity_ref=gap.id,
            insight_type="reconciliation_gap_high",
            severity="HIGH",
            title=f"Gap aberto HIGH: {gap.gap_type}",
            detail={"gap_type": gap.gap_type, "order_id": gap.order_id},
            suggested_action="Resolver na aba Gaps ou sincronizar com billing_fiscal_service.",
        ):
            created += 1

    for evt in db.query(FiscalContingencyEvent).filter(FiscalContingencyEvent.active.is_(True)).all():
        if _upsert_insight(
            db,
            entity_type="contingency",
            entity_ref=evt.id,
            insight_type="contingency_active",
            severity="CRITICAL",
            title=f"Contingência {evt.contingency_mode} — {evt.authority}",
            detail={
                "country": evt.country,
                "region_code": evt.region_code,
                "mode": evt.contingency_mode,
                "issuer_code": evt.issuer_code,
            },
            suggested_action="Emitir em modo contingência (SVC-AN/EPEC); monitorar retorno SEFAZ.",
        ):
            created += 1

    db.commit()
    return {"insights_created": created, "insights_open": db.query(FiscalOpsInsight).filter(FiscalOpsInsight.status == "OPEN").count()}


def intelligence_dashboard(db: Session) -> dict:
    today = date.today()
    certs_expiring = (
        db.query(FiscalComplianceCertification)
        .filter(
            FiscalComplianceCertification.expires_at.isnot(None),
            FiscalComplianceCertification.expires_at <= today + timedelta(days=90),
            FiscalComplianceCertification.expires_at >= today,
        )
        .count()
    )
    certs_expired = (
        db.query(FiscalComplianceCertification)
        .filter(
            FiscalComplianceCertification.expires_at.isnot(None),
            FiscalComplianceCertification.expires_at < today,
        )
        .count()
    )
    return {
        "open_insights": db.query(FiscalOpsInsight).filter(FiscalOpsInsight.status == "OPEN").count(),
        "critical_insights": db.query(FiscalOpsInsight)
        .filter(FiscalOpsInsight.status == "OPEN", FiscalOpsInsight.severity == "CRITICAL")
        .count(),
        "webhook_dlq": db.query(FiscalWebhookDeliveryLog)
        .filter(FiscalWebhookDeliveryLog.delivery_status.in_(["FAILED", "DLQ"]))
        .count(),
        "readiness_d_band": db.query(FiscalIntegrationReadiness).filter(FiscalIntegrationReadiness.readiness_band == "D").count(),
        "certs_expiring_90d": certs_expiring,
        "certs_expired": certs_expired,
        "active_contingencies": db.query(FiscalContingencyEvent).filter(FiscalContingencyEvent.active.is_(True)).count(),
        "open_gaps_high": db.query(FiscalReconciliationGap)
        .filter(FiscalReconciliationGap.status == "OPEN", FiscalReconciliationGap.severity == "HIGH")
        .count(),
    }


def list_insights(db: Session, *, status: str | None = "OPEN", limit: int = 100) -> list[FiscalOpsInsight]:
    q = db.query(FiscalOpsInsight)
    if status:
        q = q.filter(FiscalOpsInsight.status == status)
    return q.order_by(FiscalOpsInsight.severity.desc(), FiscalOpsInsight.detected_at.desc()).limit(limit).all()


def insight_to_dict(row: FiscalOpsInsight) -> dict:
    return {
        "id": row.id,
        "entity_type": row.entity_type,
        "entity_ref": row.entity_ref,
        "insight_type": row.insight_type,
        "severity": row.severity,
        "title": row.title,
        "detail": json.loads(row.detail_json or "{}"),
        "suggested_action": row.suggested_action,
        "status": row.status,
        "detected_at": row.detected_at.isoformat() if row.detected_at else None,
    }


def register_contingency(
    db: Session,
    *,
    country: str,
    authority: str,
    contingency_mode: str,
    reason: str | None = None,
    region_code: str | None = None,
    issuer_code: str | None = None,
) -> FiscalContingencyEvent:
    row = FiscalContingencyEvent(
        id=new_id(),
        country=country.upper(),
        region_code=region_code,
        authority=authority,
        contingency_mode=contingency_mode.upper(),
        reason=reason,
        issuer_code=issuer_code,
        active=True,
        started_at=_utcnow(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def close_contingency(db: Session, event_id: str) -> FiscalContingencyEvent | None:
    row = db.get(FiscalContingencyEvent, event_id)
    if not row:
        return None
    row.active = False
    row.ended_at = _utcnow()
    db.commit()
    db.refresh(row)
    return row


def list_contingencies(db: Session, *, active_only: bool = True, limit: int = 50) -> list[FiscalContingencyEvent]:
    q = db.query(FiscalContingencyEvent)
    if active_only:
        q = q.filter(FiscalContingencyEvent.active.is_(True))
    return q.order_by(FiscalContingencyEvent.started_at.desc()).limit(limit).all()


def contingency_to_dict(row: FiscalContingencyEvent) -> dict:
    return {
        "id": row.id,
        "country": row.country,
        "region_code": row.region_code,
        "authority": row.authority,
        "contingency_mode": row.contingency_mode,
        "reason": row.reason,
        "issuer_code": row.issuer_code,
        "active": row.active,
        "started_at": row.started_at.isoformat() if row.started_at else None,
        "ended_at": row.ended_at.isoformat() if row.ended_at else None,
    }


def get_corridor_detail(db: Session, corridor_code: str) -> dict | None:
    corridor = db.query(FiscalTaxCorridor).filter(FiscalTaxCorridor.corridor_code == corridor_code).first()
    if not corridor:
        return None
    rules = (
        db.query(FiscalCorridorTaxRule)
        .filter(FiscalCorridorTaxRule.corridor_id == corridor.id)
        .order_by(FiscalCorridorTaxRule.rule_order)
        .all()
    )
    return {
        "corridor_code": corridor.corridor_code,
        "name": corridor.name,
        "origin_country": corridor.origin_country,
        "dest_country": corridor.dest_country,
        "primary_issuer_code": corridor.primary_issuer_code,
        "fallback_issuer_code": corridor.fallback_issuer_code,
        "document_type_code": corridor.document_type_code,
        "handoff_type": corridor.handoff_type,
        "service_level": corridor.service_level,
        "transit_hours_max": corridor.transit_hours_max,
        "notes": corridor.notes,
        "tax_rules": [
            {
                "rule_order": r.rule_order,
                "tax_code": r.tax_code,
                "rate_pct": float(r.rate_pct) if r.rate_pct is not None else None,
                "cfop": r.cfop,
                "ncm_pattern": r.ncm_pattern,
            }
            for r in rules
        ],
    }


def list_certifications_enriched(
    db: Session,
    *,
    issuer_id: str | None = None,
    expiring_within_days: int | None = None,
) -> list[dict]:
    rows = db.query(FiscalComplianceCertification).order_by(FiscalComplianceCertification.expires_at).all()
    if issuer_id:
        rows = [r for r in rows if r.issuer_id == issuer_id]
    out: list[dict] = []
    today = date.today()
    for r in rows:
        severity = cert_expiry_severity(r.expires_at, within_days=expiring_within_days or 90)
        if expiring_within_days is not None and r.expires_at:
            if r.expires_at > today + timedelta(days=expiring_within_days):
                continue
        days_left = (r.expires_at - today).days if r.expires_at else None
        out.append(
            {
                "id": r.id,
                "issuer_code": r.issuer_code,
                "certification_type": r.certification_type,
                "status": r.status,
                "issuer_authority": r.issuer_authority,
                "expires_at": r.expires_at.isoformat() if r.expires_at else None,
                "expiry_severity": severity,
                "days_until_expiry": days_left,
            }
        )
    return out


def retry_webhook_delivery(db: Session, delivery_id: str) -> FiscalWebhookDeliveryLog | None:
    row = db.get(FiscalWebhookDeliveryLog, delivery_id)
    if not row:
        return None
    if row.delivery_status not in ("FAILED", "DLQ"):
        return row
    row.delivery_status = "PENDING"
    row.attempt = (row.attempt or 0) + 1
    row.next_retry_at = _utcnow()
    row.error_message = None
    db.commit()
    db.refresh(row)
    return row


def test_classify_sku(db: Session, *, sku: str, country: str = "BR") -> dict:
    rules = (
        db.query(FiscalAutoClassificationRule)
        .filter(FiscalAutoClassificationRule.active.is_(True), FiscalAutoClassificationRule.country == country.upper())
        .order_by(FiscalAutoClassificationRule.priority)
        .all()
    )
    matched: FiscalAutoClassificationRule | None = None
    for rule in rules:
        if fnmatch.fnmatch(sku.upper(), rule.sku_pattern.upper().replace("%", "*")):
            matched = rule
            break
    if not matched:
        return {"sku": sku, "country": country, "matched": False, "message": "Nenhuma regra encontrada"}
    return {
        "sku": sku,
        "country": country,
        "matched": True,
        "rule_id": matched.id,
        "sku_pattern": matched.sku_pattern,
        "ncm_code": matched.ncm_code,
        "cfop": matched.cfop,
        "icms_cst": matched.icms_cst,
        "pis_cst": matched.pis_cst,
        "cofins_cst": matched.cofins_cst,
        "source": matched.source,
    }


def seed_demo_intelligence(db: Session) -> dict[str, int]:
    """Demo: cert expiring soon + contingency event for intelligence scan."""
    counts = {"cert_patched": 0, "contingency": 0}
    cert = (
        db.query(FiscalComplianceCertification)
        .filter(FiscalComplianceCertification.certification_type == "A1")
        .first()
    )
    if cert:
        cert.expires_at = date.today() + timedelta(days=45)
        cert.status = "VALID"
        counts["cert_patched"] = 1

    if not db.get(FiscalContingencyEvent, "cont-demo-br-sp"):
        db.add(
            FiscalContingencyEvent(
                id="cont-demo-br-sp",
                country="BR",
                region_code="SP",
                authority="SEFAZ-SP",
                contingency_mode="SVC-AN",
                reason="Demo: indisponibilidade SEFAZ para testes de intelligence",
                issuer_code="SEFAZ-BR-SP",
                active=False,
                started_at=_utcnow() - timedelta(hours=2),
                ended_at=_utcnow() - timedelta(hours=1),
            )
        )
        counts["contingency"] = 1

    db.commit()
    return counts
