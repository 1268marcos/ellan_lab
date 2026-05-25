from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.critical_table_context import get_actor_context
from app.core.database import get_db
from shared.security.critical_table_guard import ActorContext
from app.schemas.privacy import (
    ApiKeyListOut,
    ApiKeyRotateOut,
    ConsentIn,
    ConsentListOut,
    ConsentOut,
    ConsentUpdate,
    DashboardOut,
    DeletionRequestIn,
    DeletionRequestListOut,
    DeletionRequestOut,
    DeletionRequestUpdate,
    PolicyVersionIn,
    PolicyVersionListOut,
    PolicyVersionOut,
    PolicyVersionUpdate,
    RegulationIn,
    RegulationListOut,
    RegulationOut,
    RegulationUpdate,
    SubjectRequestIn,
    SubjectRequestListOut,
    SubjectRequestOut,
    SubjectRequestUpdate,
    WebhookIn,
    WebhookListOut,
    WebhookOut,
    WebhookUpdate,
)
from app.services import privacy_service as svc

router = APIRouter(tags=["privacy-compliance"])


@router.get("/dashboard", response_model=DashboardOut)
def get_dashboard(db: Session = Depends(get_db)) -> DashboardOut:
    return svc.dashboard(db)


@router.get("/regulations", response_model=RegulationListOut)
def list_regulations(
    active_only: bool = Query(False),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
) -> RegulationListOut:
    items = [RegulationOut.model_validate(r) for r in svc.list_regulations(db, active_only=active_only, limit=limit)]
    return RegulationListOut(items=items, total=len(items))


@router.post("/regulations", response_model=RegulationOut, status_code=status.HTTP_201_CREATED)
def create_regulation(body: RegulationIn, db: Session = Depends(get_db)) -> RegulationOut:
    return RegulationOut.model_validate(svc.create_regulation(db, body))


@router.get("/regulations/{regulation_id}", response_model=RegulationOut)
def get_regulation(regulation_id: str, db: Session = Depends(get_db)) -> RegulationOut:
    return RegulationOut.model_validate(svc.get_regulation_or_404(db, regulation_id))


@router.patch("/regulations/{regulation_id}", response_model=RegulationOut)
def update_regulation(
    regulation_id: str, body: RegulationUpdate, db: Session = Depends(get_db)
) -> RegulationOut:
    return RegulationOut.model_validate(svc.update_regulation(db, regulation_id, body))


@router.delete("/regulations/{regulation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_regulation(regulation_id: str, db: Session = Depends(get_db)) -> None:
    svc.delete_regulation(db, regulation_id)


@router.get("/policy-versions", response_model=PolicyVersionListOut)
def list_policy_versions(
    regulation_id: str | None = Query(None),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
) -> PolicyVersionListOut:
    items = [
        PolicyVersionOut.model_validate(r)
        for r in svc.list_policy_versions(db, regulation_id=regulation_id, limit=limit)
    ]
    return PolicyVersionListOut(items=items, total=len(items))


@router.post("/policy-versions", response_model=PolicyVersionOut, status_code=status.HTTP_201_CREATED)
def create_policy_version(body: PolicyVersionIn, db: Session = Depends(get_db)) -> PolicyVersionOut:
    return PolicyVersionOut.model_validate(svc.create_policy_version(db, body))


@router.patch("/policy-versions/{policy_id}", response_model=PolicyVersionOut)
def update_policy_version(
    policy_id: str, body: PolicyVersionUpdate, db: Session = Depends(get_db)
) -> PolicyVersionOut:
    return PolicyVersionOut.model_validate(svc.update_policy_version(db, policy_id, body))


@router.delete("/policy-versions/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_policy_version(policy_id: str, db: Session = Depends(get_db)) -> None:
    svc.delete_policy_version(db, policy_id)


@router.get("/consents", response_model=ConsentListOut)
def list_consents(
    regulation_code: str | None = Query(None),
    consent_type: str | None = Query(None),
    user_id: str | None = Query(None),
    limit: int = Query(200, le=500),
    db: Session = Depends(get_db),
    actor: ActorContext = Depends(get_actor_context),
) -> ConsentListOut:
    items = [
        ConsentOut.model_validate(r)
        for r in svc.list_consents(
            db,
            regulation_code=regulation_code,
            consent_type=consent_type,
            user_id=user_id,
            limit=limit,
            actor=actor,
        )
    ]
    return ConsentListOut(items=items, total=len(items))


@router.post("/consents", response_model=ConsentOut, status_code=status.HTTP_201_CREATED)
def create_consent(
    body: ConsentIn,
    db: Session = Depends(get_db),
    actor: ActorContext = Depends(get_actor_context),
) -> ConsentOut:
    return ConsentOut.model_validate(svc.create_consent(db, body, actor=actor))


@router.patch("/consents/{consent_id}", response_model=ConsentOut)
def update_consent(
    consent_id: str,
    body: ConsentUpdate,
    db: Session = Depends(get_db),
    actor: ActorContext = Depends(get_actor_context),
) -> ConsentOut:
    return ConsentOut.model_validate(svc.update_consent(db, consent_id, body, actor=actor))


@router.delete("/consents/{consent_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_consent(
    consent_id: str,
    db: Session = Depends(get_db),
    actor: ActorContext = Depends(get_actor_context),
) -> None:
    svc.delete_consent(db, consent_id, actor=actor)


@router.get("/deletion-requests", response_model=DeletionRequestListOut)
def list_deletion_requests(
    regulation_code: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(200, le=500),
    db: Session = Depends(get_db),
) -> DeletionRequestListOut:
    items = [
        DeletionRequestOut.model_validate(r)
        for r in svc.list_deletion_requests(
            db, regulation_code=regulation_code, status_filter=status_filter, limit=limit
        )
    ]
    return DeletionRequestListOut(items=items, total=len(items))


@router.post("/deletion-requests", response_model=DeletionRequestOut, status_code=status.HTTP_201_CREATED)
def create_deletion_request(body: DeletionRequestIn, db: Session = Depends(get_db)) -> DeletionRequestOut:
    return DeletionRequestOut.model_validate(svc.create_deletion_request(db, body))


@router.patch("/deletion-requests/{request_id}", response_model=DeletionRequestOut)
def update_deletion_request(
    request_id: str, body: DeletionRequestUpdate, db: Session = Depends(get_db)
) -> DeletionRequestOut:
    return DeletionRequestOut.model_validate(svc.update_deletion_request(db, request_id, body))


@router.delete("/deletion-requests/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_deletion_request(request_id: str, db: Session = Depends(get_db)) -> None:
    svc.delete_deletion_request(db, request_id)


@router.get("/subject-requests", response_model=SubjectRequestListOut)
def list_subject_requests(
    regulation_code: str | None = Query(None),
    request_type: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(200, le=500),
    db: Session = Depends(get_db),
) -> SubjectRequestListOut:
    items = [
        SubjectRequestOut.model_validate(r)
        for r in svc.list_subject_requests(
            db,
            regulation_code=regulation_code,
            request_type=request_type,
            status_filter=status_filter,
            limit=limit,
        )
    ]
    return SubjectRequestListOut(items=items, total=len(items))


@router.post("/subject-requests", response_model=SubjectRequestOut, status_code=status.HTTP_201_CREATED)
def create_subject_request(body: SubjectRequestIn, db: Session = Depends(get_db)) -> SubjectRequestOut:
    return SubjectRequestOut.model_validate(svc.create_subject_request(db, body))


@router.patch("/subject-requests/{request_id}", response_model=SubjectRequestOut)
def update_subject_request(
    request_id: str, body: SubjectRequestUpdate, db: Session = Depends(get_db)
) -> SubjectRequestOut:
    return SubjectRequestOut.model_validate(svc.update_subject_request(db, request_id, body))


@router.delete("/subject-requests/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subject_request(request_id: str, db: Session = Depends(get_db)) -> None:
    svc.delete_subject_request(db, request_id)


@router.get("/webhooks", response_model=WebhookListOut)
def list_webhooks(
    regulation_code: str | None = Query(None),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
) -> WebhookListOut:
    items = svc.list_webhooks(db, regulation_code=regulation_code, limit=limit)
    return WebhookListOut(items=items, total=len(items))


@router.put("/webhooks", response_model=WebhookOut)
def upsert_webhook(body: WebhookIn, db: Session = Depends(get_db)) -> WebhookOut:
    return svc.upsert_webhook(db, body)


@router.patch("/webhooks/{webhook_id}", response_model=WebhookOut)
def update_webhook(webhook_id: str, body: WebhookUpdate, db: Session = Depends(get_db)) -> WebhookOut:
    return svc.update_webhook(db, webhook_id, body)


@router.delete("/webhooks/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_webhook(webhook_id: str, db: Session = Depends(get_db)) -> None:
    svc.delete_webhook(db, webhook_id)


@router.post("/regulations/{regulation_code}/api-keys/rotate", response_model=ApiKeyRotateOut)
def rotate_api_key(regulation_code: str, db: Session = Depends(get_db)) -> ApiKeyRotateOut:
    return svc.rotate_api_key(db, regulation_code)


@router.get("/regulations/{regulation_code}/api-keys", response_model=ApiKeyListOut)
def list_api_keys(regulation_code: str, db: Session = Depends(get_db)) -> ApiKeyListOut:
    return svc.list_api_keys(db, regulation_code)
