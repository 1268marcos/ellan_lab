from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.cross_domain import WebhookDeliveryListOut, WebhookDeliveryOut
from app.services import cross_domain_service

router = APIRouter(prefix="/webhook-deliveries", tags=["webhook-deliveries"])


@router.get("", response_model=WebhookDeliveryListOut)
def list_items(
    endpoint_id: str | None = Query(None),
    status: str | None = Query(None),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
) -> WebhookDeliveryListOut:
    items = cross_domain_service.list_webhook_deliveries(
        db, endpoint_id=endpoint_id, status=status, limit=limit
    )
    out = [WebhookDeliveryOut.model_validate(i) for i in items]
    return WebhookDeliveryListOut(items=out, total=len(out))


@router.post("/{delivery_id}/retry", response_model=WebhookDeliveryOut)
def retry(delivery_id: str, db: Session = Depends(get_db)) -> WebhookDeliveryOut:
    return WebhookDeliveryOut.model_validate(cross_domain_service.retry_webhook_delivery(db, delivery_id))
