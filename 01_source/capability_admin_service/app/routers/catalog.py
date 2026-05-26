from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.capability import (
    CapabilityChannel,
    CapabilityContext,
    CapabilityRegion,
    PaymentInterfaceCatalog,
    PaymentMethodCatalog,
    WalletProviderCatalog,
    CapabilityRequirementCatalog,
)
from app.schemas.common import (
    CatalogMethodIn,
    ChannelIn,
    ChannelOut,
    ContextIn,
    ContextOut,
    ListOut,
    OrmModel,
    RegionIn,
    RegionOut,
)
from app.services.serialize import row_to_dict

router = APIRouter(tags=["catalog"])


class RequirementOut(OrmModel):
    id: int
    code: str
    name: str
    data_type: str
    is_active: bool


@router.get("/channels", response_model=ListOut)
def list_channels(db: Session = Depends(get_db)) -> ListOut:
    items = db.query(CapabilityChannel).order_by(CapabilityChannel.code).all()
    return ListOut(items=[ChannelOut.model_validate(i) for i in items], total=len(items))


@router.post("/channels", response_model=ChannelOut, status_code=status.HTTP_201_CREATED)
def create_channel(body: ChannelIn, db: Session = Depends(get_db)) -> ChannelOut:
    row = CapabilityChannel(**body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return ChannelOut.model_validate(row)


@router.patch("/channels/{item_id}", response_model=ChannelOut)
def update_channel(item_id: int, body: ChannelIn, db: Session = Depends(get_db)) -> ChannelOut:
    row = db.get(CapabilityChannel, item_id)
    if not row:
        raise HTTPException(status_code=404, detail="not_found")
    for k, v in body.model_dump().items():
        setattr(row, k, v)
    db.commit()
    db.refresh(row)
    return ChannelOut.model_validate(row)


@router.get("/contexts", response_model=ListOut)
def list_contexts(channel_id: int | None = None, db: Session = Depends(get_db)) -> ListOut:
    q = db.query(CapabilityContext)
    if channel_id:
        q = q.filter(CapabilityContext.channel_id == channel_id)
    items = q.order_by(CapabilityContext.code).all()
    return ListOut(items=[ContextOut.model_validate(i) for i in items], total=len(items))


@router.post("/contexts", response_model=ContextOut, status_code=status.HTTP_201_CREATED)
def create_context(body: ContextIn, db: Session = Depends(get_db)) -> ContextOut:
    row = CapabilityContext(**body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return ContextOut.model_validate(row)


@router.get("/regions", response_model=ListOut)
def list_regions(db: Session = Depends(get_db)) -> ListOut:
    items = db.query(CapabilityRegion).order_by(CapabilityRegion.code).all()
    return ListOut(items=[RegionOut.model_validate(i) for i in items], total=len(items))


@router.post("/regions", response_model=RegionOut, status_code=status.HTTP_201_CREATED)
def create_region(body: RegionIn, db: Session = Depends(get_db)) -> RegionOut:
    row = CapabilityRegion(**body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return RegionOut.model_validate(row)


@router.get("/payment-methods", response_model=ListOut)
def list_payment_methods(active_only: bool = Query(False), db: Session = Depends(get_db)) -> ListOut:
    q = db.query(PaymentMethodCatalog)
    if active_only:
        q = q.filter(PaymentMethodCatalog.is_active.is_(True))
    items = q.order_by(PaymentMethodCatalog.code).all()
    return ListOut(items=[row_to_dict(i) for i in items], total=len(items))


@router.post("/payment-methods", status_code=status.HTTP_201_CREATED)
def create_payment_method(body: CatalogMethodIn, db: Session = Depends(get_db)):
    row = PaymentMethodCatalog(**body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row_to_dict(row)


@router.get("/payment-interfaces", response_model=ListOut)
def list_interfaces(db: Session = Depends(get_db)) -> ListOut:
    items = db.query(PaymentInterfaceCatalog).order_by(PaymentInterfaceCatalog.code).all()
    return ListOut(items=[row_to_dict(i) for i in items], total=len(items))


@router.get("/wallet-providers", response_model=ListOut)
def list_wallets(db: Session = Depends(get_db)) -> ListOut:
    items = db.query(WalletProviderCatalog).order_by(WalletProviderCatalog.code).all()
    return ListOut(items=[row_to_dict(i) for i in items], total=len(items))


@router.get("/requirements", response_model=ListOut)
def list_requirements(db: Session = Depends(get_db)) -> ListOut:
    items = db.query(CapabilityRequirementCatalog).order_by(CapabilityRequirementCatalog.code).all()
    return ListOut(items=[RequirementOut.model_validate(i) for i in items], total=len(items))
