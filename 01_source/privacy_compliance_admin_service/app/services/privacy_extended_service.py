from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.privacy import DataDeletionRequest, DataSubjectRequest, PrivacyConsent, PrivacyRegulation
from app.models.privacy_extended import (
    PrivacyActivityProcessorLink,
    PrivacyBreachIncident,
    PrivacyDataCategory,
    PrivacyImpactAssessment,
    PrivacyLegalBasis,
    PrivacyProcessingActivity,
    PrivacyProcessor,
    PrivacyProcessorAgreement,
    PrivacyRetentionRule,
    PrivacyTransferRecord,
)
from app.schemas.privacy_extended import (
    BreachIncidentIn,
    BreachIncidentUpdate,
    DataCategoryIn,
    ImpactAssessmentIn,
    ImpactAssessmentUpdate,
    LegalBasisIn,
    ProcessingActivityIn,
    ProcessingActivityUpdate,
    ProcessorAgreementIn,
    ProcessorIn,
    RegulationHubOut,
    RetentionRuleIn,
    TransferRecordIn,
)
from app.services.crypto_util import new_id, parse_events_json, utcnow


def _json_list(raw: str | None) -> list[str]:
    return parse_events_json(raw)


def _dump_list(items: list[str]) -> str:
    return json.dumps(items)


def get_regulation_by_code(db: Session, code: str) -> PrivacyRegulation:
    row = db.query(PrivacyRegulation).filter(PrivacyRegulation.code == code.upper()).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="regulation_not_found")
    return row


def _activity_out(row: PrivacyProcessingActivity) -> dict:
    return {
        "id": row.id,
        "regulation_code": row.regulation_code,
        "code": row.code,
        "name": row.name,
        "purpose": row.purpose,
        "data_controller": row.data_controller,
        "legal_basis_id": row.legal_basis_id,
        "data_categories": _json_list(row.data_categories_json),
        "recipients": _json_list(row.recipients_json),
        "retention_days": row.retention_days,
        "cross_border": row.cross_border,
        "status": row.status,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def _processor_out(row: PrivacyProcessor) -> dict:
    return {
        "id": row.id,
        "name": row.name,
        "processor_type": row.processor_type,
        "country": row.country,
        "contact_email": row.contact_email,
        "services": _json_list(row.services_json),
        "regulation_codes": _json_list(row.regulation_codes_json),
        "active": row.active,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def regulation_hub(db: Session, regulation_code: str) -> RegulationHubOut:
    reg = get_regulation_by_code(db, regulation_code)
    code = reg.code
    processor_ids = [
        p.id
        for p in db.query(PrivacyProcessor).all()
        if code in _json_list(p.regulation_codes_json)
    ]
    return RegulationHubOut(
        regulation_code=code,
        regulation_name=reg.name,
        jurisdiction=reg.jurisdiction,
        processing_activities=db.query(PrivacyProcessingActivity).filter_by(regulation_code=code).count(),
        legal_bases=db.query(PrivacyLegalBasis).filter_by(regulation_code=code, active=True).count(),
        data_categories=db.query(PrivacyDataCategory).filter_by(regulation_code=code, active=True).count(),
        processors=len(processor_ids),
        active_dpas=db.query(PrivacyProcessorAgreement)
        .filter(PrivacyProcessorAgreement.regulation_code == code, PrivacyProcessorAgreement.status == "ACTIVE")
        .count(),
        retention_rules=db.query(PrivacyRetentionRule).filter_by(regulation_code=code, active=True).count(),
        open_breaches=db.query(PrivacyBreachIncident)
        .filter(PrivacyBreachIncident.regulation_code == code, PrivacyBreachIncident.status == "OPEN")
        .count(),
        dpia_pending=db.query(PrivacyImpactAssessment)
        .filter(PrivacyImpactAssessment.regulation_code == code, PrivacyImpactAssessment.status.in_(["DRAFT", "REVIEW"]))
        .count(),
        active_transfers=db.query(PrivacyTransferRecord)
        .filter(PrivacyTransferRecord.regulation_code == code, PrivacyTransferRecord.status == "ACTIVE")
        .count(),
        pending_dsar=db.query(DataSubjectRequest)
        .filter(DataSubjectRequest.regulation_code == code, DataSubjectRequest.status == "PENDING")
        .count(),
        pending_deletions=db.query(DataDeletionRequest)
        .filter(DataDeletionRequest.regulation_code == code, DataDeletionRequest.status == "PENDING")
        .count(),
        active_consents=db.query(PrivacyConsent)
        .filter(
            PrivacyConsent.regulation_code == code,
            PrivacyConsent.granted.is_(True),
            PrivacyConsent.revoked_at.is_(None),
        )
        .count(),
    )


def list_legal_bases(db: Session, *, regulation_code: str | None = None, limit: int = 200) -> list[PrivacyLegalBasis]:
    q = db.query(PrivacyLegalBasis)
    if regulation_code:
        q = q.filter(PrivacyLegalBasis.regulation_code == regulation_code.upper())
    return q.order_by(PrivacyLegalBasis.regulation_code, PrivacyLegalBasis.code).limit(limit).all()


def create_legal_basis(db: Session, body: LegalBasisIn) -> PrivacyLegalBasis:
    get_regulation_by_code(db, body.regulation_code)
    row = PrivacyLegalBasis(
        id=new_id(),
        regulation_code=body.regulation_code.upper(),
        code=body.code.upper(),
        name=body.name,
        article_ref=body.article_ref,
        description=body.description,
        requires_consent=body.requires_consent,
        created_at=utcnow(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_data_categories(db: Session, *, regulation_code: str | None = None, limit: int = 200) -> list[PrivacyDataCategory]:
    q = db.query(PrivacyDataCategory)
    if regulation_code:
        q = q.filter(PrivacyDataCategory.regulation_code == regulation_code.upper())
    return q.order_by(PrivacyDataCategory.regulation_code, PrivacyDataCategory.code).limit(limit).all()


def create_data_category(db: Session, body: DataCategoryIn) -> PrivacyDataCategory:
    get_regulation_by_code(db, body.regulation_code)
    row = PrivacyDataCategory(
        id=new_id(),
        regulation_code=body.regulation_code.upper(),
        code=body.code.upper(),
        name=body.name,
        sensitivity=body.sensitivity.upper(),
        description=body.description,
        special_category=body.special_category,
        created_at=utcnow(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_processing_activities(
    db: Session, *, regulation_code: str | None = None, limit: int = 200
) -> list[dict]:
    q = db.query(PrivacyProcessingActivity)
    if regulation_code:
        q = q.filter(PrivacyProcessingActivity.regulation_code == regulation_code.upper())
    return [_activity_out(r) for r in q.order_by(PrivacyProcessingActivity.code).limit(limit).all()]


def create_processing_activity(db: Session, body: ProcessingActivityIn) -> dict:
    get_regulation_by_code(db, body.regulation_code)
    now = utcnow()
    row = PrivacyProcessingActivity(
        id=new_id(),
        regulation_code=body.regulation_code.upper(),
        code=body.code.upper(),
        name=body.name,
        purpose=body.purpose,
        data_controller=body.data_controller,
        legal_basis_id=body.legal_basis_id,
        data_categories_json=_dump_list(body.data_categories),
        recipients_json=_dump_list(body.recipients),
        retention_days=body.retention_days,
        cross_border=body.cross_border,
        status=body.status.upper(),
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _activity_out(row)


def update_processing_activity(db: Session, activity_id: str, body: ProcessingActivityUpdate) -> dict:
    row = db.get(PrivacyProcessingActivity, activity_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="processing_activity_not_found")
    data = body.model_dump(exclude_unset=True)
    if "data_categories" in data:
        row.data_categories_json = _dump_list(data.pop("data_categories"))
    if "recipients" in data:
        row.recipients_json = _dump_list(data.pop("recipients"))
    for k, v in data.items():
        setattr(row, k, v)
    row.updated_at = utcnow()
    db.commit()
    db.refresh(row)
    return _activity_out(row)


def list_processors(db: Session, *, regulation_code: str | None = None, limit: int = 200) -> list[dict]:
    rows = db.query(PrivacyProcessor).order_by(PrivacyProcessor.name).limit(limit).all()
    if regulation_code:
        code = regulation_code.upper()
        rows = [r for r in rows if code in _json_list(r.regulation_codes_json)]
    return [_processor_out(r) for r in rows]


def create_processor(db: Session, body: ProcessorIn) -> dict:
    for code in body.regulation_codes:
        get_regulation_by_code(db, code)
    now = utcnow()
    row = PrivacyProcessor(
        id=new_id(),
        name=body.name,
        processor_type=body.processor_type.upper(),
        country=body.country,
        contact_email=body.contact_email,
        services_json=_dump_list(body.services),
        regulation_codes_json=_dump_list([c.upper() for c in body.regulation_codes]),
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _processor_out(row)


def list_processor_agreements(
    db: Session, *, regulation_code: str | None = None, processor_id: str | None = None, limit: int = 200
) -> list[PrivacyProcessorAgreement]:
    q = db.query(PrivacyProcessorAgreement)
    if regulation_code:
        q = q.filter(PrivacyProcessorAgreement.regulation_code == regulation_code.upper())
    if processor_id:
        q = q.filter(PrivacyProcessorAgreement.processor_id == processor_id)
    return q.order_by(PrivacyProcessorAgreement.created_at.desc()).limit(limit).all()


def create_processor_agreement(db: Session, body: ProcessorAgreementIn) -> PrivacyProcessorAgreement:
    get_regulation_by_code(db, body.regulation_code)
    if not db.get(PrivacyProcessor, body.processor_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="processor_not_found")
    now = utcnow()
    row = PrivacyProcessorAgreement(
        id=new_id(),
        processor_id=body.processor_id,
        regulation_code=body.regulation_code.upper(),
        agreement_type=body.agreement_type.upper(),
        status=body.status.upper(),
        signed_at=body.signed_at,
        expires_at=body.expires_at,
        document_url=body.document_url,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_retention_rules(db: Session, *, regulation_code: str | None = None, limit: int = 200) -> list[PrivacyRetentionRule]:
    q = db.query(PrivacyRetentionRule)
    if regulation_code:
        q = q.filter(PrivacyRetentionRule.regulation_code == regulation_code.upper())
    return q.order_by(PrivacyRetentionRule.retention_days).limit(limit).all()


def create_retention_rule(db: Session, body: RetentionRuleIn) -> PrivacyRetentionRule:
    get_regulation_by_code(db, body.regulation_code)
    row = PrivacyRetentionRule(
        id=new_id(),
        regulation_code=body.regulation_code.upper(),
        data_category_id=body.data_category_id,
        processing_activity_id=body.processing_activity_id,
        retention_days=body.retention_days,
        purge_method=body.purge_method.upper(),
        legal_basis_code=body.legal_basis_code,
        notes=body.notes,
        created_at=utcnow(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_breach_incidents(db: Session, *, regulation_code: str | None = None, limit: int = 200) -> list[PrivacyBreachIncident]:
    q = db.query(PrivacyBreachIncident)
    if regulation_code:
        q = q.filter(PrivacyBreachIncident.regulation_code == regulation_code.upper())
    return q.order_by(PrivacyBreachIncident.discovered_at.desc()).limit(limit).all()


def create_breach_incident(db: Session, body: BreachIncidentIn) -> PrivacyBreachIncident:
    get_regulation_by_code(db, body.regulation_code)
    now = utcnow()
    row = PrivacyBreachIncident(
        id=new_id(),
        regulation_code=body.regulation_code.upper(),
        title=body.title,
        severity=body.severity.upper(),
        status="OPEN",
        discovered_at=body.discovered_at,
        affected_count=body.affected_count,
        description=body.description,
        notification_required=body.notification_required,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_breach_incident(db: Session, incident_id: str, body: BreachIncidentUpdate) -> PrivacyBreachIncident:
    row = db.get(PrivacyBreachIncident, incident_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="breach_not_found")
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(row, k, v)
    row.updated_at = utcnow()
    db.commit()
    db.refresh(row)
    return row


def list_impact_assessments(
    db: Session, *, regulation_code: str | None = None, limit: int = 200
) -> list[PrivacyImpactAssessment]:
    q = db.query(PrivacyImpactAssessment)
    if regulation_code:
        q = q.filter(PrivacyImpactAssessment.regulation_code == regulation_code.upper())
    return q.order_by(PrivacyImpactAssessment.created_at.desc()).limit(limit).all()


def create_impact_assessment(db: Session, body: ImpactAssessmentIn) -> PrivacyImpactAssessment:
    get_regulation_by_code(db, body.regulation_code)
    now = utcnow()
    row = PrivacyImpactAssessment(
        id=new_id(),
        regulation_code=body.regulation_code.upper(),
        processing_activity_id=body.processing_activity_id,
        title=body.title,
        risk_level=body.risk_level.upper(),
        status="DRAFT",
        reviewer=body.reviewer,
        mitigation_summary=body.mitigation_summary,
        document_url=body.document_url,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_impact_assessment(db: Session, assessment_id: str, body: ImpactAssessmentUpdate) -> PrivacyImpactAssessment:
    row = db.get(PrivacyImpactAssessment, assessment_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="dpia_not_found")
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(row, k, v)
    row.updated_at = utcnow()
    db.commit()
    db.refresh(row)
    return row


def list_transfer_records(
    db: Session, *, regulation_code: str | None = None, limit: int = 200
) -> list[PrivacyTransferRecord]:
    q = db.query(PrivacyTransferRecord)
    if regulation_code:
        q = q.filter(PrivacyTransferRecord.regulation_code == regulation_code.upper())
    return q.order_by(PrivacyTransferRecord.destination_country).limit(limit).all()


def create_transfer_record(db: Session, body: TransferRecordIn) -> PrivacyTransferRecord:
    get_regulation_by_code(db, body.regulation_code)
    now = utcnow()
    row = PrivacyTransferRecord(
        id=new_id(),
        regulation_code=body.regulation_code.upper(),
        destination_country=body.destination_country.upper(),
        mechanism=body.mechanism.upper(),
        processor_id=body.processor_id,
        processing_activity_id=body.processing_activity_id,
        status="ACTIVE",
        document_ref=body.document_ref,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def extended_dashboard_counts(db: Session) -> dict[str, int]:
    return {
        "processing_activities": db.query(PrivacyProcessingActivity).count(),
        "legal_bases": db.query(PrivacyLegalBasis).filter(PrivacyLegalBasis.active.is_(True)).count(),
        "data_categories": db.query(PrivacyDataCategory).filter(PrivacyDataCategory.active.is_(True)).count(),
        "processors": db.query(PrivacyProcessor).filter(PrivacyProcessor.active.is_(True)).count(),
        "active_dpas": db.query(PrivacyProcessorAgreement).filter(PrivacyProcessorAgreement.status == "ACTIVE").count(),
        "retention_rules": db.query(PrivacyRetentionRule).filter(PrivacyRetentionRule.active.is_(True)).count(),
        "open_breaches": db.query(PrivacyBreachIncident).filter(PrivacyBreachIncident.status == "OPEN").count(),
        "dpia_pending": db.query(PrivacyImpactAssessment)
        .filter(PrivacyImpactAssessment.status.in_(["DRAFT", "REVIEW"]))
        .count(),
        "active_transfers": db.query(PrivacyTransferRecord).filter(PrivacyTransferRecord.status == "ACTIVE").count(),
    }
