from __future__ import annotations

import json
from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.privacy import (
    DataDeletionRequest,
    DataSubjectRequest,
    PrivacyApiKey,
    PrivacyConsent,
    PrivacyPolicyVersion,
    PrivacyRegulation,
    PrivacyWebhookEndpoint,
)
from app.schemas.privacy import (
    ApiKeyListOut,
    ApiKeyMetaOut,
    ApiKeyRotateOut,
    ConsentIn,
    ConsentUpdate,
    DashboardOut,
    DeletionRequestIn,
    DeletionRequestUpdate,
    PolicyVersionIn,
    PolicyVersionUpdate,
    RegulationIn,
    RegulationUpdate,
    SubjectRequestIn,
    SubjectRequestUpdate,
    WebhookIn,
    WebhookOut,
    WebhookUpdate,
)
from app.services.critical_table_security_service import enforce
from app.services.crypto_util import generate_privacy_api_key, new_id, parse_events_json, utcnow
from shared.security.critical_table_guard import ActorContext


def get_regulation_or_404(db: Session, regulation_id: str) -> PrivacyRegulation:
    row = db.get(PrivacyRegulation, regulation_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="regulation_not_found")
    return row


def get_regulation_by_code_or_404(db: Session, code: str) -> PrivacyRegulation:
    row = db.query(PrivacyRegulation).filter(PrivacyRegulation.code == code.upper()).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="regulation_not_found")
    return row


from app.services.privacy_extended_service import extended_dashboard_counts


def dashboard(db: Session) -> DashboardOut:
    pending_del = db.query(DataDeletionRequest).filter(DataDeletionRequest.status == "PENDING").count()
    pending_sub = db.query(DataSubjectRequest).filter(DataSubjectRequest.status == "PENDING").count()
    granted = db.query(PrivacyConsent).filter(PrivacyConsent.granted.is_(True), PrivacyConsent.revoked_at.is_(None)).count()
    revoked = db.query(PrivacyConsent).filter(PrivacyConsent.revoked_at.isnot(None)).count()
    ext = extended_dashboard_counts(db)
    return DashboardOut(
        regulations=db.query(PrivacyRegulation).count(),
        active_policies=db.query(PrivacyPolicyVersion).filter(PrivacyPolicyVersion.is_current.is_(True)).count(),
        pending_deletions=pending_del,
        pending_subject_requests=pending_sub,
        consents_granted=granted,
        consents_revoked=revoked,
        webhooks_active=db.query(PrivacyWebhookEndpoint).filter(PrivacyWebhookEndpoint.active.is_(True)).count(),
        **ext,
    )


def list_regulations(db: Session, *, active_only: bool = False, limit: int = 100) -> list[PrivacyRegulation]:
    q = db.query(PrivacyRegulation)
    if active_only:
        q = q.filter(PrivacyRegulation.active.is_(True))
    return q.order_by(PrivacyRegulation.code).limit(limit).all()


def create_regulation(db: Session, body: RegulationIn) -> PrivacyRegulation:
    code = body.code.upper()
    if db.query(PrivacyRegulation).filter(PrivacyRegulation.code == code).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="regulation_code_exists")
    now = utcnow()
    row = PrivacyRegulation(
        id=new_id(),
        code=code,
        name=body.name,
        jurisdiction=body.jurisdiction,
        description=body.description,
        dpo_email=body.dpo_email,
        supervisory_authority=body.supervisory_authority,
        default_retention_days=body.default_retention_days,
        response_sla_days=body.response_sla_days,
        active=body.active,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_regulation(db: Session, regulation_id: str, body: RegulationUpdate) -> PrivacyRegulation:
    row = get_regulation_or_404(db, regulation_id)
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(row, k, v)
    row.updated_at = utcnow()
    db.commit()
    db.refresh(row)
    return row


def delete_regulation(db: Session, regulation_id: str) -> None:
    row = get_regulation_or_404(db, regulation_id)
    db.delete(row)
    db.commit()


def list_policy_versions(
    db: Session, *, regulation_id: str | None = None, limit: int = 100
) -> list[PrivacyPolicyVersion]:
    q = db.query(PrivacyPolicyVersion)
    if regulation_id:
        q = q.filter(PrivacyPolicyVersion.regulation_id == regulation_id)
    return q.order_by(PrivacyPolicyVersion.effective_at.desc()).limit(limit).all()


def create_policy_version(db: Session, body: PolicyVersionIn) -> PrivacyPolicyVersion:
    get_regulation_or_404(db, body.regulation_id)
    if body.is_current:
        db.query(PrivacyPolicyVersion).filter(
            PrivacyPolicyVersion.regulation_id == body.regulation_id,
            PrivacyPolicyVersion.is_current.is_(True),
        ).update({"is_current": False})
    row = PrivacyPolicyVersion(
        id=new_id(),
        regulation_id=body.regulation_id,
        version=body.version,
        title=body.title,
        content_url=body.content_url,
        summary=body.summary,
        effective_at=body.effective_at,
        is_current=body.is_current,
        created_at=utcnow(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_policy_version(db: Session, policy_id: str, body: PolicyVersionUpdate) -> PrivacyPolicyVersion:
    row = db.get(PrivacyPolicyVersion, policy_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="policy_not_found")
    data = body.model_dump(exclude_unset=True)
    if data.get("is_current"):
        db.query(PrivacyPolicyVersion).filter(
            PrivacyPolicyVersion.regulation_id == row.regulation_id,
            PrivacyPolicyVersion.is_current.is_(True),
            PrivacyPolicyVersion.id != policy_id,
        ).update({"is_current": False})
    for k, v in data.items():
        setattr(row, k, v)
    db.commit()
    db.refresh(row)
    return row


def delete_policy_version(db: Session, policy_id: str) -> None:
    row = db.get(PrivacyPolicyVersion, policy_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="policy_not_found")
    db.delete(row)
    db.commit()


def list_consents(
    db: Session,
    *,
    regulation_code: str | None = None,
    consent_type: str | None = None,
    user_id: str | None = None,
    limit: int = 200,
    actor: ActorContext | None = None,
) -> list[PrivacyConsent]:
    ctx = actor or ActorContext(roles=["admin_operacao"])
    enforce(db, table_name="privacy_consents", operation="SELECT", actor=ctx, target_user_id=user_id)
    q = db.query(PrivacyConsent)
    if regulation_code:
        q = q.filter(PrivacyConsent.regulation_code == regulation_code.upper())
    if consent_type:
        q = q.filter(PrivacyConsent.consent_type == consent_type)
    if user_id:
        q = q.filter(PrivacyConsent.user_id == user_id)
    return q.order_by(PrivacyConsent.created_at.desc()).limit(limit).all()


def create_consent(db: Session, body: ConsentIn, *, actor: ActorContext | None = None) -> PrivacyConsent:
    ctx = actor or ActorContext(roles=["admin_operacao"])
    enforce(
        db,
        table_name="privacy_consents",
        operation="INSERT",
        actor=ctx,
        target_user_id=body.user_id,
    )
    get_regulation_by_code_or_404(db, body.regulation_code)
    now = utcnow()
    row = PrivacyConsent(
        id=new_id(),
        user_id=body.user_id,
        guest_identifier=body.guest_identifier,
        regulation_code=body.regulation_code.upper(),
        consent_type=body.consent_type,
        granted=body.granted,
        channel=body.channel,
        ip_address=body.ip_address,
        user_agent=body.user_agent,
        policy_version=body.policy_version,
        granted_at=now,
        revoked_at=None if body.granted else now,
        created_at=now,
        recorded_by_service=ctx.service_name,
        access_policy_version=1,
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    try:
        from app.services.webhook_dispatcher_service import dispatch_delivery, enqueue_webhook_event

        event = "consent.granted" if row.granted and not row.revoked_at else "consent.revoked"
        delivery = enqueue_webhook_event(
            db,
            regulation_code=row.regulation_code,
            event_name=event,
            payload={"consent_id": row.id, "consent_type": row.consent_type, "granted": row.granted},
            aggregate_id=row.id,
        )
        dispatch_delivery(db, delivery.id)
    except Exception:
        pass

    return row


def update_consent(
    db: Session, consent_id: str, body: ConsentUpdate, *, actor: ActorContext | None = None
) -> PrivacyConsent:
    row = db.get(PrivacyConsent, consent_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="consent_not_found")
    ctx = actor or ActorContext(roles=["admin_operacao"])
    enforce(
        db,
        table_name="privacy_consents",
        operation="UPDATE",
        actor=ctx,
        target_user_id=row.user_id,
        row_id=consent_id,
    )
    data = body.model_dump(exclude_unset=True)
    if "granted" in data and data["granted"] is False and "revoked_at" not in data:
        row.revoked_at = utcnow()
    if "granted" in data and data["granted"] is True:
        row.revoked_at = None
    for k, v in data.items():
        setattr(row, k, v)
    db.commit()
    db.refresh(row)
    return row


def delete_consent(db: Session, consent_id: str, *, actor: ActorContext | None = None) -> None:
    row = db.get(PrivacyConsent, consent_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="consent_not_found")
    ctx = actor or ActorContext(roles=["admin_operacao"])
    enforce(
        db,
        table_name="privacy_consents",
        operation="DELETE",
        actor=ctx,
        target_user_id=row.user_id,
        row_id=consent_id,
    )
    db.delete(row)
    db.commit()


def list_deletion_requests(
    db: Session, *, regulation_code: str | None = None, status_filter: str | None = None, limit: int = 200
) -> list[DataDeletionRequest]:
    q = db.query(DataDeletionRequest)
    if regulation_code:
        q = q.filter(DataDeletionRequest.regulation_code == regulation_code.upper())
    if status_filter:
        q = q.filter(DataDeletionRequest.status == status_filter.upper())
    return q.order_by(DataDeletionRequest.requested_at.desc()).limit(limit).all()


def create_deletion_request(db: Session, body: DeletionRequestIn) -> DataDeletionRequest:
    get_regulation_by_code_or_404(db, body.regulation_code)
    now = utcnow()
    row = DataDeletionRequest(
        id=new_id(),
        regulation_code=body.regulation_code.upper(),
        user_id=body.user_id,
        requested_by=body.requested_by,
        status="PENDING",
        reason=body.reason,
        notes=body.notes,
        requested_at=now,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_deletion_request(db: Session, request_id: str, body: DeletionRequestUpdate) -> DataDeletionRequest:
    row = db.get(DataDeletionRequest, request_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="deletion_request_not_found")
    data = body.model_dump(exclude_unset=True)
    if data.get("status") == "COMPLETED" and "completed_at" not in data:
        row.completed_at = utcnow()
    for k, v in data.items():
        setattr(row, k, v)
    row.updated_at = utcnow()
    db.commit()
    db.refresh(row)
    return row


def delete_deletion_request(db: Session, request_id: str) -> None:
    row = db.get(DataDeletionRequest, request_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="deletion_request_not_found")
    db.delete(row)
    db.commit()


def list_subject_requests(
    db: Session,
    *,
    regulation_code: str | None = None,
    request_type: str | None = None,
    status_filter: str | None = None,
    limit: int = 200,
) -> list[DataSubjectRequest]:
    q = db.query(DataSubjectRequest)
    if regulation_code:
        q = q.filter(DataSubjectRequest.regulation_code == regulation_code.upper())
    if request_type:
        q = q.filter(DataSubjectRequest.request_type == request_type.upper())
    if status_filter:
        q = q.filter(DataSubjectRequest.status == status_filter.upper())
    return q.order_by(DataSubjectRequest.created_at.desc()).limit(limit).all()


def create_subject_request(db: Session, body: SubjectRequestIn) -> DataSubjectRequest:
    reg = get_regulation_by_code_or_404(db, body.regulation_code)
    now = utcnow()
    row = DataSubjectRequest(
        id=new_id(),
        regulation_code=body.regulation_code.upper(),
        user_id=body.user_id,
        guest_identifier=body.guest_identifier,
        request_type=body.request_type.upper(),
        status="PENDING",
        requested_by=body.requested_by,
        details=body.details,
        due_at=now + timedelta(days=reg.response_sla_days),
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_subject_request(db: Session, request_id: str, body: SubjectRequestUpdate) -> DataSubjectRequest:
    row = db.get(DataSubjectRequest, request_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="subject_request_not_found")
    data = body.model_dump(exclude_unset=True)
    if data.get("status") == "COMPLETED" and "completed_at" not in data:
        row.completed_at = utcnow()
    for k, v in data.items():
        setattr(row, k, v)
    row.updated_at = utcnow()
    db.commit()
    db.refresh(row)
    return row


def delete_subject_request(db: Session, request_id: str) -> None:
    row = db.get(DataSubjectRequest, request_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="subject_request_not_found")
    db.delete(row)
    db.commit()


def _webhook_out(row: PrivacyWebhookEndpoint) -> WebhookOut:
    return WebhookOut(
        id=row.id,
        regulation_code=row.regulation_code,
        url=row.url,
        events=parse_events_json(row.events_json),
        signing_algo=row.signing_algo,
        active=row.active,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def list_webhooks(db: Session, *, regulation_code: str | None = None, limit: int = 100) -> list[WebhookOut]:
    q = db.query(PrivacyWebhookEndpoint)
    if regulation_code:
        q = q.filter(PrivacyWebhookEndpoint.regulation_code == regulation_code.upper())
    rows = q.order_by(PrivacyWebhookEndpoint.created_at.desc()).limit(limit).all()
    return [_webhook_out(r) for r in rows]


def upsert_webhook(db: Session, body: WebhookIn) -> WebhookOut:
    get_regulation_by_code_or_404(db, body.regulation_code)
    code = body.regulation_code.upper()
    row = db.query(PrivacyWebhookEndpoint).filter(PrivacyWebhookEndpoint.regulation_code == code).first()
    now = utcnow()
    events_json = json.dumps(body.events)
    secret_ref = body.secret[:64] if body.secret else None
    if row:
        row.url = body.url
        row.events_json = events_json
        row.secret_ref = secret_ref or row.secret_ref
        row.signing_algo = body.signing_algo
        row.active = body.active
        row.updated_at = now
    else:
        row = PrivacyWebhookEndpoint(
            id=new_id(),
            regulation_code=code,
            url=body.url,
            events_json=events_json,
            secret_ref=secret_ref,
            signing_algo=body.signing_algo,
            active=body.active,
            created_at=now,
            updated_at=now,
        )
        db.add(row)
    db.commit()
    db.refresh(row)
    return _webhook_out(row)


def update_webhook(db: Session, webhook_id: str, body: WebhookUpdate) -> WebhookOut:
    row = db.get(PrivacyWebhookEndpoint, webhook_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="webhook_not_found")
    data = body.model_dump(exclude_unset=True)
    if "events" in data and data["events"] is not None:
        row.events_json = json.dumps(data.pop("events"))
    if "secret" in data:
        secret = data.pop("secret")
        if secret:
            row.secret_ref = secret[:64]
    for k, v in data.items():
        setattr(row, k, v)
    row.updated_at = utcnow()
    db.commit()
    db.refresh(row)
    return _webhook_out(row)


def delete_webhook(db: Session, webhook_id: str) -> None:
    row = db.get(PrivacyWebhookEndpoint, webhook_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="webhook_not_found")
    db.delete(row)
    db.commit()


def rotate_api_key(db: Session, regulation_code: str) -> ApiKeyRotateOut:
    get_regulation_by_code_or_404(db, regulation_code)
    code = regulation_code.upper()
    now = utcnow()
    db.query(PrivacyApiKey).filter(
        PrivacyApiKey.regulation_code == code,
        PrivacyApiKey.revoked_at.is_(None),
    ).update({"revoked_at": now})
    api_key, prefix, key_hash = generate_privacy_api_key(code)
    row = PrivacyApiKey(
        id=new_id(),
        regulation_code=code,
        key_prefix=prefix,
        key_hash=key_hash,
        label="rotated",
        created_at=now,
    )
    db.add(row)
    db.commit()
    return ApiKeyRotateOut(regulation_code=code, api_key=api_key, key_prefix=prefix, created_at=now)


def list_api_keys(db: Session, regulation_code: str) -> ApiKeyListOut:
    get_regulation_by_code_or_404(db, regulation_code)
    code = regulation_code.upper()
    rows = (
        db.query(PrivacyApiKey)
        .filter(PrivacyApiKey.regulation_code == code)
        .order_by(PrivacyApiKey.created_at.desc())
        .all()
    )
    return ApiKeyListOut(
        regulation_code=code,
        keys=[
            ApiKeyMetaOut(
                id=row.id,
                key_prefix=row.key_prefix,
                label=row.label,
                revoked_at=row.revoked_at,
                created_at=row.created_at,
            )
            for row in rows
        ],
    )
