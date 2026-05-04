from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import get_idempotency_store, idempotency_key_header
from app.schemas.reservation import ReservationCreate, ReservationOut
from app.services import reservation_service
from app.services.idempotency import IdempotencyStore
from metrics.inventory_metrics import inc_reservation

router = APIRouter(prefix="/api/v1", tags=["reservations"])


@router.post("/reservations", response_model=ReservationOut, status_code=status.HTTP_201_CREATED)
def create_reservation(
    body: ReservationCreate,
    db: Session = Depends(get_db),
    store: IdempotencyStore = Depends(get_idempotency_store),
    idem: str | None = Depends(idempotency_key_header),
) -> ReservationOut:
    try:
        r = reservation_service.create_reservation(db, body.order_id, body.sku_id, body.quantity, store, idem)
    except ValueError as e:
        if str(e) == "insufficient_stock":
            raise HTTPException(status_code=409, detail="insufficient_stock") from e
        raise
    inc_reservation(r.state)
    return r


@router.post("/reservations/{reservation_id}/confirm", response_model=ReservationOut)
def confirm_reservation(
    reservation_id: str,
    db: Session = Depends(get_db),
    version: int = Query(..., ge=1),
) -> ReservationOut:
    try:
        return reservation_service.confirm_reservation(db, reservation_id, version)
    except ValueError as e:
        msg = str(e)
        if msg == "not_found":
            raise HTTPException(status_code=404, detail=msg) from e
        if msg in ("version_mismatch", "invalid_state"):
            raise HTTPException(status_code=409, detail=msg) from e
        raise


@router.delete("/reservations/{reservation_id}", response_model=ReservationOut)
def release_reservation(
    reservation_id: str,
    db: Session = Depends(get_db),
    store: IdempotencyStore = Depends(get_idempotency_store),
    version: int = Query(..., ge=1),
) -> ReservationOut:
    try:
        return reservation_service.release_reservation(db, reservation_id, version, store)
    except ValueError as e:
        msg = str(e)
        if msg == "not_found":
            raise HTTPException(status_code=404, detail=msg) from e
        if msg in ("version_mismatch", "invalid_state"):
            raise HTTPException(status_code=409, detail=msg) from e
        raise
