from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.cross_domain import (
    HardwareCrossDomainDashboardOut,
    HardwareDomainReferenceIn,
    HardwareDomainReferenceListOut,
    HardwareDomainReferenceOut,
    HardwareDomainReferenceUpdate,
    HardwareEcosystemPlayerIn,
    HardwareEcosystemPlayerListOut,
    HardwareEcosystemPlayerOut,
    HardwareEcosystemPlayerUpdate,
    HardwareLockerCarrierBindingIn,
    HardwareLockerCarrierBindingListOut,
    HardwareLockerCarrierBindingOut,
    HardwareLockerCarrierBindingUpdate,
    HardwareLockerMarketplaceLinkIn,
    HardwareLockerMarketplaceLinkListOut,
    HardwareLockerMarketplaceLinkOut,
    HardwareLockerMarketplaceLinkUpdate,
    HardwareLockerPaymentBindingIn,
    HardwareLockerPaymentBindingListOut,
    HardwareLockerPaymentBindingOut,
    HardwareLockerPaymentBindingUpdate,
)
from app.schemas.cross_domain_links import (
    CrossDomainGapsScanOut,
    DomainReferenceVerificationOut,
    EcosystemAlignmentOut,
    Locker360Out,
    PaymentBindingSyncOut,
)
from app.services import cross_domain_link_service
from app.services import cross_domain_service

router = APIRouter(prefix="/cross-domain", tags=["cross-domain"])


@router.get("/dashboard", response_model=HardwareCrossDomainDashboardOut)
def cross_domain_dashboard(db: Session = Depends(get_db)) -> HardwareCrossDomainDashboardOut:
    return cross_domain_service.get_dashboard(db)


@router.post("/ecosystem-players/seed-catalog")
def seed_ecosystem_catalog(db: Session = Depends(get_db)) -> dict[str, int]:
    from app.services.seed_data import seed_ecosystem_players

    return {"inserted": seed_ecosystem_players(db)}


@router.get("/ecosystem-players", response_model=HardwareEcosystemPlayerListOut)
def list_ecosystem_players(
    segment: str | None = Query(None), db: Session = Depends(get_db)
) -> HardwareEcosystemPlayerListOut:
    items = cross_domain_service.list_ecosystem_players(db, segment=segment)
    out = [HardwareEcosystemPlayerOut.model_validate(i) for i in items]
    return HardwareEcosystemPlayerListOut(items=out, total=len(out))


@router.post("/ecosystem-players", response_model=HardwareEcosystemPlayerOut, status_code=status.HTTP_201_CREATED)
def create_ecosystem_player(
    body: HardwareEcosystemPlayerIn, db: Session = Depends(get_db)
) -> HardwareEcosystemPlayerOut:
    return HardwareEcosystemPlayerOut.model_validate(cross_domain_service.create_ecosystem_player(db, body))


@router.get("/marketplace-links", response_model=HardwareLockerMarketplaceLinkListOut)
def list_marketplace_links(
    locker_id: str | None = Query(None), db: Session = Depends(get_db)
) -> HardwareLockerMarketplaceLinkListOut:
    items = cross_domain_service.list_marketplace_links(db, locker_id=locker_id)
    out = [HardwareLockerMarketplaceLinkOut.model_validate(i) for i in items]
    return HardwareLockerMarketplaceLinkListOut(items=out, total=len(out))


@router.post("/marketplace-links", response_model=HardwareLockerMarketplaceLinkOut, status_code=status.HTTP_201_CREATED)
def create_marketplace_link(
    body: HardwareLockerMarketplaceLinkIn, db: Session = Depends(get_db)
) -> HardwareLockerMarketplaceLinkOut:
    return HardwareLockerMarketplaceLinkOut.model_validate(cross_domain_service.create_marketplace_link(db, body))


@router.get("/payment-bindings", response_model=HardwareLockerPaymentBindingListOut)
def list_payment_bindings(
    locker_id: str | None = Query(None), db: Session = Depends(get_db)
) -> HardwareLockerPaymentBindingListOut:
    items = cross_domain_service.list_payment_bindings(db, locker_id=locker_id)
    out = [HardwareLockerPaymentBindingOut.model_validate(i) for i in items]
    return HardwareLockerPaymentBindingListOut(items=out, total=len(out))


@router.post("/payment-bindings", response_model=HardwareLockerPaymentBindingOut, status_code=status.HTTP_201_CREATED)
def create_payment_binding(
    body: HardwareLockerPaymentBindingIn, db: Session = Depends(get_db)
) -> HardwareLockerPaymentBindingOut:
    return HardwareLockerPaymentBindingOut.model_validate(cross_domain_service.create_payment_binding(db, body))


@router.get("/carrier-bindings", response_model=HardwareLockerCarrierBindingListOut)
def list_carrier_bindings(
    locker_id: str | None = Query(None), db: Session = Depends(get_db)
) -> HardwareLockerCarrierBindingListOut:
    items = cross_domain_service.list_carrier_bindings(db, locker_id=locker_id)
    out = [HardwareLockerCarrierBindingOut.model_validate(i) for i in items]
    return HardwareLockerCarrierBindingListOut(items=out, total=len(out))


@router.post("/carrier-bindings", response_model=HardwareLockerCarrierBindingOut, status_code=status.HTTP_201_CREATED)
def create_carrier_binding(
    body: HardwareLockerCarrierBindingIn, db: Session = Depends(get_db)
) -> HardwareLockerCarrierBindingOut:
    return HardwareLockerCarrierBindingOut.model_validate(cross_domain_service.create_carrier_binding(db, body))


@router.get("/domain-references", response_model=HardwareDomainReferenceListOut)
def list_domain_references(
    locker_id: str | None = Query(None),
    domain_type: str | None = Query(None),
    db: Session = Depends(get_db),
) -> HardwareDomainReferenceListOut:
    items = cross_domain_service.list_domain_references(db, locker_id=locker_id, domain_type=domain_type)
    out = [HardwareDomainReferenceOut.model_validate(i) for i in items]
    return HardwareDomainReferenceListOut(items=out, total=len(out))


@router.post("/domain-references", response_model=HardwareDomainReferenceOut, status_code=status.HTTP_201_CREATED)
def create_domain_reference(
    body: HardwareDomainReferenceIn, db: Session = Depends(get_db)
) -> HardwareDomainReferenceOut:
    return HardwareDomainReferenceOut.model_validate(cross_domain_service.create_domain_reference(db, body))


@router.get("/lockers/{locker_id}/360", response_model=Locker360Out)
def locker_cross_domain_360(locker_id: str, db: Session = Depends(get_db)) -> Locker360Out:
    return cross_domain_link_service.get_locker_360(db, locker_id)


@router.get("/gaps-scan", response_model=CrossDomainGapsScanOut)
def scan_cross_domain_gaps(
    locker_id: str | None = Query(None), db: Session = Depends(get_db)
) -> CrossDomainGapsScanOut:
    return cross_domain_link_service.scan_cross_domain_gaps(db, locker_id=locker_id)


@router.post("/domain-references/verify", response_model=list[DomainReferenceVerificationOut])
def verify_domain_references(
    locker_id: str | None = Query(None), db: Session = Depends(get_db)
) -> list[DomainReferenceVerificationOut]:
    return cross_domain_link_service.verify_domain_references(db, locker_id=locker_id)


@router.post("/payment-bindings/sync-from-gateway", response_model=PaymentBindingSyncOut)
def sync_payment_bindings_from_gateway(
    locker_id: str | None = Query(None),
    dry_run: bool = Query(False),
    db: Session = Depends(get_db),
) -> PaymentBindingSyncOut:
    return cross_domain_link_service.sync_payment_bindings_from_gateway(
        db, locker_id=locker_id, dry_run=dry_run
    )


@router.post("/ecosystem-players/align-partner", response_model=EcosystemAlignmentOut)
def align_ecosystem_with_partner(
    apply: bool = Query(False), db: Session = Depends(get_db)
) -> EcosystemAlignmentOut:
    return cross_domain_link_service.align_ecosystem_with_partner(db, apply=apply)


@router.patch("/ecosystem-players/{player_id}", response_model=HardwareEcosystemPlayerOut)
def update_ecosystem_player(
    player_id: str, body: HardwareEcosystemPlayerUpdate, db: Session = Depends(get_db)
) -> HardwareEcosystemPlayerOut:
    return HardwareEcosystemPlayerOut.model_validate(
        cross_domain_service.update_ecosystem_player(db, player_id, body)
    )


@router.delete("/ecosystem-players/{player_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ecosystem_player(player_id: str, db: Session = Depends(get_db)) -> None:
    cross_domain_service.delete_ecosystem_player(db, player_id)


@router.patch("/marketplace-links/{link_id}", response_model=HardwareLockerMarketplaceLinkOut)
def update_marketplace_link(
    link_id: str, body: HardwareLockerMarketplaceLinkUpdate, db: Session = Depends(get_db)
) -> HardwareLockerMarketplaceLinkOut:
    return HardwareLockerMarketplaceLinkOut.model_validate(
        cross_domain_service.update_marketplace_link(db, link_id, body)
    )


@router.delete("/marketplace-links/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_marketplace_link(link_id: str, db: Session = Depends(get_db)) -> None:
    cross_domain_service.delete_marketplace_link(db, link_id)


@router.patch("/payment-bindings/{binding_id}", response_model=HardwareLockerPaymentBindingOut)
def update_payment_binding(
    binding_id: str, body: HardwareLockerPaymentBindingUpdate, db: Session = Depends(get_db)
) -> HardwareLockerPaymentBindingOut:
    return HardwareLockerPaymentBindingOut.model_validate(
        cross_domain_service.update_payment_binding(db, binding_id, body)
    )


@router.delete("/payment-bindings/{binding_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payment_binding(binding_id: str, db: Session = Depends(get_db)) -> None:
    cross_domain_service.delete_payment_binding(db, binding_id)


@router.patch("/carrier-bindings/{binding_id}", response_model=HardwareLockerCarrierBindingOut)
def update_carrier_binding(
    binding_id: str, body: HardwareLockerCarrierBindingUpdate, db: Session = Depends(get_db)
) -> HardwareLockerCarrierBindingOut:
    return HardwareLockerCarrierBindingOut.model_validate(
        cross_domain_service.update_carrier_binding(db, binding_id, body)
    )


@router.delete("/carrier-bindings/{binding_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_carrier_binding(binding_id: str, db: Session = Depends(get_db)) -> None:
    cross_domain_service.delete_carrier_binding(db, binding_id)


@router.patch("/domain-references/{ref_id}", response_model=HardwareDomainReferenceOut)
def update_domain_reference(
    ref_id: str, body: HardwareDomainReferenceUpdate, db: Session = Depends(get_db)
) -> HardwareDomainReferenceOut:
    return HardwareDomainReferenceOut.model_validate(
        cross_domain_service.update_domain_reference(db, ref_id, body)
    )


@router.delete("/domain-references/{ref_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_domain_reference(ref_id: str, db: Session = Depends(get_db)) -> None:
    cross_domain_service.delete_domain_reference(db, ref_id)
