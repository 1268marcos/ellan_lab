from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.cross_domain import PaymentEcosystemSegment
from app.schemas.ecosystem_pro import EcosystemSegmentListOut, EcosystemSegmentOut

router = APIRouter(prefix="/ecosystem-segments", tags=["ecosystem-segments"])


@router.get("", response_model=EcosystemSegmentListOut)
def list_segments(db: Session = Depends(get_db)) -> EcosystemSegmentListOut:
    items = (
        db.query(PaymentEcosystemSegment)
        .filter(PaymentEcosystemSegment.is_active.is_(True))
        .order_by(PaymentEcosystemSegment.sort_order)
        .all()
    )
    out = [EcosystemSegmentOut.model_validate(i) for i in items]
    return EcosystemSegmentListOut(items=out, total=len(out))
