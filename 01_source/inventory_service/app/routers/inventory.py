from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import get_idempotency_store, idempotency_key_header
from app.events.publisher import publish_event
from app.models.inventory import Locker, ProductInventory
from app.schemas.inventory import InventoryOut, LockerCreate, LockerOut, MovementCreate
from app.services import inventory_service
from app.services.idempotency import IdempotencyStore

router = APIRouter(prefix="/api/v1", tags=["inventory"])


@router.get("/inventory/{sku_id}", response_model=InventoryOut)
def get_inventory(sku_id: str, db: Session = Depends(get_db)) -> ProductInventory:
    inv = inventory_service.get_or_create_inventory(db, sku_id)
    return inv


@router.post("/inventory/movements", status_code=status.HTTP_201_CREATED)
def create_movement(
    request: Request,
    body: MovementCreate,
    db: Session = Depends(get_db),
    store: IdempotencyStore = Depends(get_idempotency_store),
    idem: str | None = Depends(idempotency_key_header),
) -> dict:
    try:
        m, inv = inventory_service.apply_movement(
            db, body.sku_id, body.delta, body.reason, idem, store, getattr(request.app.state, "redis", None)
        )
    except ValueError as e:
        if str(e) == "insufficient_stock":
            raise HTTPException(status_code=409, detail="insufficient_stock") from e
        raise
    r = getattr(request.app.state, "redis", None)
    publish_event(r, "inventory.movement", {"sku_id": body.sku_id, "movement_id": m.id})
    return {"movement_id": m.id, "sku_id": inv.sku_id, "quantity_on_hand": inv.quantity_on_hand, "version": inv.version}


@router.post("/lockers", response_model=LockerOut, status_code=status.HTTP_201_CREATED)
def create_locker(body: LockerCreate, db: Session = Depends(get_db)) -> Locker:
    lk = Locker(site_id=body.site_id, name=body.name, capacity_units=body.capacity_units)
    db.add(lk)
    db.commit()
    db.refresh(lk)
    return lk
