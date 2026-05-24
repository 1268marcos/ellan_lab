from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.domain_hub import (
    CrossDomainGapsOut,
    PaymentCrossDomainEventListOut,
    PaymentCrossDomainEventOut,
    PaymentDomainObligationIn,
    PaymentDomainObligationListOut,
    PaymentDomainObligationOut,
    PaymentDomainObligationUpdate,
    PaymentDomainRegistryListOut,
    PaymentDomainRegistryOut,
    PaymentExternalReferenceIn,
    PaymentExternalReferenceListOut,
    PaymentExternalReferenceOut,
    PaymentOrder360Out,
)
from app.services import domain_hub_service

router = APIRouter(prefix="/cross-domain", tags=["cross-domain"])


@router.get("/registry", response_model=PaymentDomainRegistryListOut)
def list_registry(db: Session = Depends(get_db)) -> PaymentDomainRegistryListOut:
    items = domain_hub_service.list_domain_registry(db)
    out = [PaymentDomainRegistryOut.model_validate(i) for i in items]
    return PaymentDomainRegistryListOut(items=out, total=len(out))


@router.get("/external-references", response_model=PaymentExternalReferenceListOut)
def list_refs(
    order_id: str | None = Query(None),
    external_domain: str | None = Query(None),
    limit: int = Query(200, le=500),
    db: Session = Depends(get_db),
) -> PaymentExternalReferenceListOut:
    items = domain_hub_service.list_external_references(
        db, order_id=order_id, external_domain=external_domain, limit=limit
    )
    out = [PaymentExternalReferenceOut.model_validate(i) for i in items]
    return PaymentExternalReferenceListOut(items=out, total=len(out))


@router.post(
    "/external-references",
    response_model=PaymentExternalReferenceOut,
    status_code=status.HTTP_201_CREATED,
)
def create_ref(body: PaymentExternalReferenceIn, db: Session = Depends(get_db)) -> PaymentExternalReferenceOut:
    return PaymentExternalReferenceOut.model_validate(
        domain_hub_service.create_external_reference(db, body)
    )


@router.delete("/external-references/{ref_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ref(ref_id: str, db: Session = Depends(get_db)) -> None:
    if not domain_hub_service.delete_external_reference(db, ref_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="reference_not_found")


@router.get("/obligations", response_model=PaymentDomainObligationListOut)
def list_obligations(
    order_id: str | None = Query(None),
    status: str | None = Query(None),
    blocking_only: bool = Query(False),
    limit: int = Query(200, le=500),
    db: Session = Depends(get_db),
) -> PaymentDomainObligationListOut:
    items = domain_hub_service.list_obligations(
        db, order_id=order_id, status=status, blocking_only=blocking_only, limit=limit
    )
    out = [PaymentDomainObligationOut.model_validate(i) for i in items]
    return PaymentDomainObligationListOut(items=out, total=len(out))


@router.post(
    "/obligations",
    response_model=PaymentDomainObligationOut,
    status_code=status.HTTP_201_CREATED,
)
def create_obligation(
    body: PaymentDomainObligationIn, db: Session = Depends(get_db)
) -> PaymentDomainObligationOut:
    return PaymentDomainObligationOut.model_validate(domain_hub_service.create_obligation(db, body))


@router.patch("/obligations/{obligation_id}", response_model=PaymentDomainObligationOut)
def update_obligation(
    obligation_id: str, body: PaymentDomainObligationUpdate, db: Session = Depends(get_db)
) -> PaymentDomainObligationOut:
    row = domain_hub_service.update_obligation(db, obligation_id, body)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="obligation_not_found")
    return PaymentDomainObligationOut.model_validate(row)


@router.get("/events", response_model=PaymentCrossDomainEventListOut)
def list_events(
    order_id: str | None = Query(None),
    status: str | None = Query(None),
    limit: int = Query(100, le=300),
    db: Session = Depends(get_db),
) -> PaymentCrossDomainEventListOut:
    items = domain_hub_service.list_cross_domain_events(
        db, order_id=order_id, status=status, limit=limit
    )
    out = [PaymentCrossDomainEventOut.model_validate(i) for i in items]
    return PaymentCrossDomainEventListOut(items=out, total=len(out))


@router.post("/events/{event_id}/publish", response_model=PaymentCrossDomainEventOut)
def publish_event(event_id: str, db: Session = Depends(get_db)) -> PaymentCrossDomainEventOut:
    row = domain_hub_service.mark_event_published(db, event_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="event_not_found")
    return PaymentCrossDomainEventOut.model_validate(row)


@router.get("/gaps", response_model=CrossDomainGapsOut)
def list_gaps(limit: int = Query(50, le=200), db: Session = Depends(get_db)) -> CrossDomainGapsOut:
    return domain_hub_service.scan_cross_domain_gaps(db, limit=limit)


@router.get("/order-360/{order_id}", response_model=PaymentOrder360Out)
def order_360(order_id: str, db: Session = Depends(get_db)) -> PaymentOrder360Out:
    result = domain_hub_service.build_order_360(db, order_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="order_not_found")
    return result
