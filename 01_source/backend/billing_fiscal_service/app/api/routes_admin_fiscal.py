from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.services.fiscal_reconciliation_service import (
    list_reconciliation_gaps,
    scan_and_persist_reconciliation_gaps,
)

router = APIRouter(prefix="/admin/fiscal", tags=["admin-fiscal"])


def validate_internal_token(internal_token: str = Header(..., alias="X-Internal-Token")):
    if internal_token != settings.internal_token:
        raise HTTPException(status_code=403, detail="Invalid internal token")


@router.get("/gaps")
def get_reconciliation_gaps(
    date: str | None = Query(default=None, description="YYYY-MM-DD"),
    status: str = Query(default="OPEN", pattern="^(OPEN|RESOLVED)?$"),
    refresh: bool = Query(default=False),
    limit: int = Query(default=200, ge=1, le=1000),
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
):
    date_from = None
    if date:
        date_from = datetime.fromisoformat(date)
    if refresh:
        scan_and_persist_reconciliation_gaps(db)
    rows = list_reconciliation_gaps(db, status=status, date_from=date_from, limit=limit)
    return {
        "count": len(rows),
        "items": [
            {
                "id": r.id,
                "dedupe_key": r.dedupe_key,
                "gap_type": r.gap_type,
                "severity": r.severity,
                "status": r.status,
                "order_id": r.order_id,
                "invoice_id": r.invoice_id,
                "details_json": r.details_json,
                "first_detected_at": r.first_detected_at.isoformat() if r.first_detected_at else None,
                "last_detected_at": r.last_detected_at.isoformat() if r.last_detected_at else None,
                "resolved_at": r.resolved_at.isoformat() if r.resolved_at else None,
            }
            for r in rows
        ],
    }
