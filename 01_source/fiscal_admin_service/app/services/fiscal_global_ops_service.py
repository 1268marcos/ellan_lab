from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.data.fiscal_global_seed import (
    CERTIFICATIONS_BY_ISSUER,
    CLASSIFICATION_RULES,
    CORRIDORS,
    DOCUMENT_TYPES,
    JURISDICTIONS,
    SLO_POLICIES,
)
from app.models.fiscal_admin import FiscalIssuerPartner
from app.models.fiscal_global import (
    FiscalAutoClassificationRule,
    FiscalComplianceCertification,
    FiscalCorridorTaxRule,
    FiscalDocumentTypeCatalog,
    FiscalEmissionSloPolicy,
    FiscalIntegrationReadiness,
    FiscalIssuerJurisdictionGrant,
    FiscalJurisdiction,
    FiscalTaxCorridor,
    FiscalWebhookDeliveryLog,
)
from app.services.crypto_util import new_id


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _issuer_map(db: Session) -> dict[str, FiscalIssuerPartner]:
    return {r.code.upper(): r for r in db.query(FiscalIssuerPartner).all()}


def seed_global_ops(db: Session) -> dict[str, int]:
    counts = {"jurisdictions": 0, "doc_types": 0, "corridors": 0, "rules": 0, "certs": 0, "slos": 0, "class_rules": 0, "grants": 0}
    issuers = _issuer_map(db)

    for j in JURISDICTIONS:
        row = db.get(FiscalJurisdiction, j["country"])
        if row:
            for k, v in j.items():
                setattr(row, k, v)
        else:
            db.add(FiscalJurisdiction(**j))
            counts["jurisdictions"] += 1

    for dt in DOCUMENT_TYPES:
        existing = db.query(FiscalDocumentTypeCatalog).filter(FiscalDocumentTypeCatalog.code == dt["code"]).first()
        if not existing:
            db.add(FiscalDocumentTypeCatalog(id=new_id(), **dt))
            counts["doc_types"] += 1

    for spec in CORRIDORS:
        primary = issuers.get(spec["primary"].upper())
        if not primary:
            continue
        fallback = issuers.get(spec["fallback"].upper()) if spec.get("fallback") else None
        row = db.query(FiscalTaxCorridor).filter(FiscalTaxCorridor.corridor_code == spec["corridor_code"]).first()
        payload = dict(
            name=spec["name"],
            origin_country=spec["origin_country"],
            dest_country=spec["dest_country"],
            primary_issuer_id=primary.id,
            primary_issuer_code=primary.code,
            fallback_issuer_id=fallback.id if fallback else None,
            fallback_issuer_code=fallback.code if fallback else None,
            document_type_code=spec["document_type_code"],
            handoff_type=spec.get("handoff_type", "LOCKER_EMISSION"),
            service_level=spec.get("service_level", "STANDARD"),
            transit_hours_max=spec.get("transit_hours_max", 72),
            active=True,
        )
        if row:
            for k, v in payload.items():
                setattr(row, k, v)
            corridor_id = row.id
        else:
            corridor_id = new_id()
            row = FiscalTaxCorridor(id=corridor_id, corridor_code=spec["corridor_code"], **payload)
            db.add(row)
            counts["corridors"] += 1
        db.flush()
        db.query(FiscalCorridorTaxRule).filter(FiscalCorridorTaxRule.corridor_id == corridor_id).delete()
        for idx, rule in enumerate(spec.get("rules", []), start=1):
            tax_code, rate, cfop, ncm = rule[0], rule[1], rule[2] if len(rule) > 2 else None, rule[3] if len(rule) > 3 else None
            db.add(
                FiscalCorridorTaxRule(
                    id=new_id(),
                    corridor_id=corridor_id,
                    rule_order=idx,
                    tax_code=tax_code,
                    rate_pct=Decimal(str(rate)) if rate is not None else None,
                    cfop=cfop,
                    ncm_pattern=ncm,
                )
            )
            counts["rules"] += 1
        grant_key = (primary.id, spec["origin_country"], spec["document_type_code"])
        if not (
            db.query(FiscalIssuerJurisdictionGrant)
            .filter(
                FiscalIssuerJurisdictionGrant.issuer_id == grant_key[0],
                FiscalIssuerJurisdictionGrant.country == grant_key[1],
                FiscalIssuerJurisdictionGrant.document_type_code == grant_key[2],
            )
            .first()
        ):
            db.add(
                FiscalIssuerJurisdictionGrant(
                    id=new_id(),
                    issuer_id=primary.id,
                    issuer_code=primary.code,
                    country=spec["origin_country"],
                    document_type_code=spec["document_type_code"],
                    grant_status="ACTIVE",
                    valid_from=date.today(),
                )
            )
            counts["grants"] += 1

    for code, items in CERTIFICATIONS_BY_ISSUER.items():
        issuer = issuers.get(code.upper())
        if not issuer:
            continue
        for cert_type, authority, status, years in items:
            issued = date.today() - timedelta(days=180)
            expires = date.today() + timedelta(days=365 * years)
            existing = (
                db.query(FiscalComplianceCertification)
                .filter(
                    FiscalComplianceCertification.issuer_id == issuer.id,
                    FiscalComplianceCertification.certification_type == cert_type,
                )
                .first()
            )
            if existing:
                existing.status = status
                existing.issuer_authority = authority
                existing.issued_at = issued
                existing.expires_at = expires
            else:
                db.add(
                    FiscalComplianceCertification(
                        id=new_id(),
                        issuer_id=issuer.id,
                        issuer_code=issuer.code,
                        certification_type=cert_type,
                        status=status,
                        issuer_authority=authority,
                        issued_at=issued,
                        expires_at=expires,
                        evidence_url=f"https://compliance.example/fiscal/{issuer.code.lower()}/{cert_type.lower()}",
                    )
                )
            counts["certs"] += 1

    for slo in SLO_POLICIES:
        if not (
            db.query(FiscalEmissionSloPolicy)
            .filter(
                FiscalEmissionSloPolicy.corridor_code == slo["corridor_code"],
                FiscalEmissionSloPolicy.metric_name == slo["metric_name"],
            )
            .first()
        ):
            db.add(FiscalEmissionSloPolicy(id=new_id(), **slo))
            counts["slos"] += 1

    for cr in CLASSIFICATION_RULES:
        if not (
            db.query(FiscalAutoClassificationRule)
            .filter(
                FiscalAutoClassificationRule.sku_pattern == cr["sku_pattern"],
                FiscalAutoClassificationRule.country == cr["country"],
            )
            .first()
        ):
            db.add(FiscalAutoClassificationRule(id=new_id(), **cr))
            counts["class_rules"] += 1

    db.commit()
    return counts


def global_ops_summary(db: Session) -> dict:
    return {
        "jurisdictions": db.query(FiscalJurisdiction).filter(FiscalJurisdiction.active.is_(True)).count(),
        "document_types": db.query(FiscalDocumentTypeCatalog).filter(FiscalDocumentTypeCatalog.active.is_(True)).count(),
        "corridors": db.query(FiscalTaxCorridor).filter(FiscalTaxCorridor.active.is_(True)).count(),
        "certifications_valid": db.query(FiscalComplianceCertification)
        .filter(FiscalComplianceCertification.status == "VALID")
        .count(),
        "webhook_failures_24h": db.query(FiscalWebhookDeliveryLog)
        .filter(FiscalWebhookDeliveryLog.delivery_status.in_(["FAILED", "DLQ"]))
        .count(),
        "readiness_a_band": db.query(FiscalIntegrationReadiness).filter(FiscalIntegrationReadiness.readiness_band == "A").count(),
    }


def list_jurisdictions(db: Session) -> list[FiscalJurisdiction]:
    return db.query(FiscalJurisdiction).order_by(FiscalJurisdiction.country).all()


def list_corridors(db: Session, active_only: bool = True) -> list[FiscalTaxCorridor]:
    q = db.query(FiscalTaxCorridor)
    if active_only:
        q = q.filter(FiscalTaxCorridor.active.is_(True))
    return q.order_by(FiscalTaxCorridor.priority, FiscalTaxCorridor.corridor_code).all()


def list_certifications(db: Session, issuer_id: str | None = None) -> list[FiscalComplianceCertification]:
    q = db.query(FiscalComplianceCertification)
    if issuer_id:
        q = q.filter(FiscalComplianceCertification.issuer_id == issuer_id)
    return q.order_by(FiscalComplianceCertification.expires_at).all()


def list_slo_policies(db: Session) -> list[FiscalEmissionSloPolicy]:
    return db.query(FiscalEmissionSloPolicy).filter(FiscalEmissionSloPolicy.active.is_(True)).all()


def list_classification_rules(db: Session, country: str | None = None) -> list[FiscalAutoClassificationRule]:
    q = db.query(FiscalAutoClassificationRule).filter(FiscalAutoClassificationRule.active.is_(True))
    if country:
        q = q.filter(FiscalAutoClassificationRule.country == country)
    return q.order_by(FiscalAutoClassificationRule.priority).all()


def list_webhook_deliveries(db: Session, failed_only: bool = False, limit: int = 100) -> list[FiscalWebhookDeliveryLog]:
    q = db.query(FiscalWebhookDeliveryLog)
    if failed_only:
        q = q.filter(FiscalWebhookDeliveryLog.delivery_status.in_(["FAILED", "DLQ"]))
    return q.order_by(FiscalWebhookDeliveryLog.created_at.desc()).limit(limit).all()


def recompute_readiness(db: Session) -> dict[str, int]:
    now = _utcnow()
    updated = 0
    for issuer in db.query(FiscalIssuerPartner).filter(FiscalIssuerPartner.active.is_(True)).all():
        certs = (
            db.query(FiscalComplianceCertification)
            .filter(
                FiscalComplianceCertification.issuer_id == issuer.id,
                FiscalComplianceCertification.status == "VALID",
            )
            .count()
        )
        score_cert = min(100.0, certs * 25.0)
        score_api = 80.0 if issuer.api_base_url else 40.0
        score_cont = 70.0 if issuer.issuer_type in ("SEFAZ", "AT_PT") else 50.0
        total = (score_cert * 0.4) + (score_api * 0.35) + (score_cont * 0.25)
        band = "A" if total >= 85 else "B" if total >= 70 else "C" if total >= 55 else "D"
        blockers: list[str] = []
        if score_cert < 50:
            blockers.append("missing_valid_certifications")
        if not issuer.api_base_url:
            blockers.append("api_base_url_not_set")
        row = db.get(FiscalIntegrationReadiness, issuer.id)
        payload = dict(
            issuer_code=issuer.code,
            country=issuer.country,
            score_total=Decimal(str(round(total, 2))),
            score_certificates=Decimal(str(round(score_cert, 2))),
            score_api=Decimal(str(round(score_api, 2))),
            score_contingency=Decimal(str(round(score_cont, 2))),
            readiness_band=band,
            blockers_json=json.dumps(blockers),
            computed_at=now,
        )
        if row:
            for k, v in payload.items():
                setattr(row, k, v)
        else:
            db.add(FiscalIntegrationReadiness(issuer_id=issuer.id, **payload))
        updated += 1
    db.commit()
    return {"updated": updated}
