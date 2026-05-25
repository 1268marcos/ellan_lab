from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.operators import LockerOperatorIn, LockerOperatorListOut, LockerOperatorOut, LockerOperatorUpdate
from app.services import operator_service

router = APIRouter(prefix="/locker-operators", tags=["locker-operators"])


@router.get("", response_model=LockerOperatorListOut)
def list_operators(
    active_only: bool = Query(False), db: Session = Depends(get_db)
) -> LockerOperatorListOut:
    items = operator_service.list_operators(db, active_only=active_only)
    out = [LockerOperatorOut.model_validate(i) for i in items]
    return LockerOperatorListOut(items=out, total=len(out))


@router.post("", response_model=LockerOperatorOut, status_code=status.HTTP_201_CREATED)
def create_operator(body: LockerOperatorIn, db: Session = Depends(get_db)) -> LockerOperatorOut:
    return LockerOperatorOut.model_validate(operator_service.create_operator(db, body))


@router.get("/{operator_id}", response_model=LockerOperatorOut)
def get_operator(operator_id: str, db: Session = Depends(get_db)) -> LockerOperatorOut:
    return LockerOperatorOut.model_validate(operator_service.get_operator_or_404(db, operator_id))


@router.patch("/{operator_id}", response_model=LockerOperatorOut)
def update_operator(
    operator_id: str, body: LockerOperatorUpdate, db: Session = Depends(get_db)
) -> LockerOperatorOut:
    return LockerOperatorOut.model_validate(operator_service.update_operator(db, operator_id, body))


@router.delete("/{operator_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_operator(operator_id: str, db: Session = Depends(get_db)) -> None:
    operator_service.delete_operator(db, operator_id)
