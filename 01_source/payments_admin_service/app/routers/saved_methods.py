from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.cross_domain import SavedPaymentMethodIn, SavedPaymentMethodListOut, SavedPaymentMethodOut
from app.services import cross_domain_service

router = APIRouter(prefix="/saved-payment-methods", tags=["saved-payment-methods"])


@router.get("", response_model=SavedPaymentMethodListOut)
def list_items(
    user_id: str | None = Query(None),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
) -> SavedPaymentMethodListOut:
    items = cross_domain_service.list_saved_methods(db, user_id=user_id, limit=limit)
    out = [SavedPaymentMethodOut.model_validate(i) for i in items]
    return SavedPaymentMethodListOut(items=out, total=len(out))


@router.post("", response_model=SavedPaymentMethodOut, status_code=status.HTTP_201_CREATED)
def create_item(body: SavedPaymentMethodIn, db: Session = Depends(get_db)) -> SavedPaymentMethodOut:
    return SavedPaymentMethodOut.model_validate(cross_domain_service.create_saved_method(db, body))


@router.delete("/{method_id}", response_model=SavedPaymentMethodOut)
def deactivate(method_id: str, db: Session = Depends(get_db)) -> SavedPaymentMethodOut:
    return SavedPaymentMethodOut.model_validate(cross_domain_service.deactivate_saved_method(db, method_id))
