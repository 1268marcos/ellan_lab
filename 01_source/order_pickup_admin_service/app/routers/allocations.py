from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.order_ops import AllocationCreateIn, AllocationListOut, AllocationOut, AllocationUpdateIn
from app.services import orders_domain_service

router = APIRouter(prefix="/allocations", tags=["allocations"])


@router.get("", response_model=AllocationListOut)
def list_allocations(
    order_id: str | None = Query(default=None),
    state: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> AllocationListOut:
    items, total = orders_domain_service.list_allocations(
        db, order_id=order_id, state=state, limit=limit, offset=offset
    )
    return AllocationListOut(items=items, total=total)


@router.post("", response_model=AllocationOut, status_code=status.HTTP_201_CREATED)
def create_allocation(body: AllocationCreateIn, db: Session = Depends(get_db)) -> AllocationOut:
    return orders_domain_service.create_allocation(db, body)


@router.patch("/{alloc_id}", response_model=AllocationOut)
def update_allocation(alloc_id: str, body: AllocationUpdateIn, db: Session = Depends(get_db)) -> AllocationOut:
    return orders_domain_service.update_allocation(db, alloc_id, body)
