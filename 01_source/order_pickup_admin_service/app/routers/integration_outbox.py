from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.order_ops import OutboxListOut, OutboxReplayOut
from app.services import order_ops_service

router = APIRouter(prefix="/integration-outbox", tags=["integration-outbox"])


@router.get("", response_model=OutboxListOut)
def list_outbox(
    status: str | None = Query(default=None),
    partner_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> OutboxListOut:
    items, total = order_ops_service.list_outbox(db, status=status, partner_id=partner_id, limit=limit, offset=offset)
    return OutboxListOut(items=items, total=total)


@router.post("/{outbox_id}/replay", response_model=OutboxReplayOut)
def replay_outbox(outbox_id: str, db: Session = Depends(get_db)) -> OutboxReplayOut:
    replayed, item = order_ops_service.replay_outbox(db, outbox_id)
    return OutboxReplayOut(ok=True, replayed=replayed, item=item)
