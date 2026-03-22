# 01_source/backend/order_lifecycle_service/app/api/routes_domain_events.py
from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.schemas.domain_events import DomainEventPublishIn, DomainEventPublishOut
from app.services.domain_event_service import publish_domain_event

router = APIRouter(prefix="/internal/domain-events", tags=["domain-events"])


def require_internal_token(x_internal_token: str = Header(..., alias="X-Internal-Token")) -> None:
    if x_internal_token != settings.internal_token:
        raise HTTPException(status_code=403, detail="invalid internal token")


@router.post("", response_model=DomainEventPublishOut)
def create_domain_event(
    payload: DomainEventPublishIn,
    _: None = Depends(require_internal_token),
    db: Session = Depends(get_db),
):
    row, idempotent = publish_domain_event(db, payload)

    return DomainEventPublishOut(
        ok=True,
        idempotent=idempotent,
        event_key=row.event_key,
        aggregate_type=row.aggregate_type,
        aggregate_id=row.aggregate_id,
        event_name=row.event_name,
        status=row.status.value if hasattr(row.status, "value") else str(row.status),
    )
