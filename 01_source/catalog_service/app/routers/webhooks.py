from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.webhook import WebhookConfigureIn, WebhookConfigureOut
from app.services import webhook_service

router = APIRouter(tags=["webhooks"])


def get_redis(request: Request) -> Any:
    return request.app.state.redis_sync


@router.post("/partners/{partner_id}/webhooks", response_model=WebhookConfigureOut)
def configure_webhook(
    partner_id: str,
    body: WebhookConfigureIn,
    redis: Any = Depends(get_redis),
    db: Session = Depends(get_db),
) -> WebhookConfigureOut:
    _ = db
    webhook_service.configure_webhook(
        redis,
        partner_id=partner_id,
        url=str(body.url),
        secret=body.secret,
        events=body.events,
    )
    return WebhookConfigureOut(partner_id=partner_id, url=str(body.url), ok=True)
