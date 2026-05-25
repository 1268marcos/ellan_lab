from __future__ import annotations

from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.assets import HardwareAsset
from app.models.cross_domain import (
    HardwareDomainReference,
    HardwareEcosystemPlayer,
    HardwareLockerCarrierBinding,
    HardwareLockerMarketplaceLink,
    HardwareLockerPaymentBinding,
)
from app.models.finance import HardwareLockerCapex, HardwareLockerOpex
from app.models.hardware_ops import HardwareSyncQueue, HardwareTelemetryEvent
from app.models.operators import LockerOperator
from app.models.runtime import HardwareDeviceRegistry, RuntimeLocker
from app.models.topology import HardwareLockerFeature, HardwareLockerSlot
from app.models.vendor import HardwareVendorPartner
from app.schemas.cross_domain import (
    HardwareCrossDomainDashboardOut,
    HardwareDomainReferenceIn,
    HardwareDomainReferenceUpdate,
    HardwareEcosystemPlayerIn,
    HardwareEcosystemPlayerUpdate,
    HardwareLockerCarrierBindingIn,
    HardwareLockerCarrierBindingUpdate,
    HardwareLockerMarketplaceLinkIn,
    HardwareLockerMarketplaceLinkUpdate,
    HardwareLockerPaymentBindingIn,
    HardwareLockerPaymentBindingUpdate,
)
from app.services.crypto_util import new_id


def list_ecosystem_players(db: Session, segment: str | None = None) -> list[HardwareEcosystemPlayer]:
    q = db.query(HardwareEcosystemPlayer)
    if segment:
        q = q.filter(HardwareEcosystemPlayer.segment == segment)
    return q.order_by(HardwareEcosystemPlayer.player_code).all()


def create_ecosystem_player(db: Session, body: HardwareEcosystemPlayerIn) -> HardwareEcosystemPlayer:
    if db.query(HardwareEcosystemPlayer).filter(HardwareEcosystemPlayer.player_code == body.player_code).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="player_code_exists")
    row = HardwareEcosystemPlayer(id=body.id or new_id(), **body.model_dump(exclude={"id"}))
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_marketplace_links(db: Session, locker_id: str | None = None) -> list[HardwareLockerMarketplaceLink]:
    q = db.query(HardwareLockerMarketplaceLink)
    if locker_id:
        q = q.filter(HardwareLockerMarketplaceLink.locker_id == locker_id)
    return q.order_by(HardwareLockerMarketplaceLink.priority).all()


def create_marketplace_link(db: Session, body: HardwareLockerMarketplaceLinkIn) -> HardwareLockerMarketplaceLink:
    row = HardwareLockerMarketplaceLink(id=new_id(), **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_payment_bindings(db: Session, locker_id: str | None = None) -> list[HardwareLockerPaymentBinding]:
    q = db.query(HardwareLockerPaymentBinding)
    if locker_id:
        q = q.filter(HardwareLockerPaymentBinding.locker_id == locker_id)
    return q.order_by(HardwareLockerPaymentBinding.priority).all()


def create_payment_binding(db: Session, body: HardwareLockerPaymentBindingIn) -> HardwareLockerPaymentBinding:
    row = HardwareLockerPaymentBinding(id=new_id(), **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_carrier_bindings(db: Session, locker_id: str | None = None) -> list[HardwareLockerCarrierBinding]:
    q = db.query(HardwareLockerCarrierBinding)
    if locker_id:
        q = q.filter(HardwareLockerCarrierBinding.locker_id == locker_id)
    return q.order_by(HardwareLockerCarrierBinding.carrier_code).all()


def create_carrier_binding(db: Session, body: HardwareLockerCarrierBindingIn) -> HardwareLockerCarrierBinding:
    row = HardwareLockerCarrierBinding(id=new_id(), **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_domain_references(db: Session, locker_id: str | None = None, domain_type: str | None = None) -> list[HardwareDomainReference]:
    q = db.query(HardwareDomainReference)
    if locker_id:
        q = q.filter(HardwareDomainReference.locker_id == locker_id)
    if domain_type:
        q = q.filter(HardwareDomainReference.domain_type == domain_type)
    return q.order_by(HardwareDomainReference.domain_type).all()


def create_domain_reference(db: Session, body: HardwareDomainReferenceIn) -> HardwareDomainReference:
    row = HardwareDomainReference(id=new_id(), **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _apply_update(row: object, body: BaseModel) -> None:
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(row, k, v)


def update_ecosystem_player(db: Session, player_id: str, body: HardwareEcosystemPlayerUpdate) -> HardwareEcosystemPlayer:
    row = db.get(HardwareEcosystemPlayer, player_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ecosystem_player_not_found")
    _apply_update(row, body)
    db.commit()
    db.refresh(row)
    return row


def delete_ecosystem_player(db: Session, player_id: str) -> None:
    row = db.get(HardwareEcosystemPlayer, player_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ecosystem_player_not_found")
    db.delete(row)
    db.commit()


def update_marketplace_link(db: Session, link_id: str, body: HardwareLockerMarketplaceLinkUpdate) -> HardwareLockerMarketplaceLink:
    row = db.get(HardwareLockerMarketplaceLink, link_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="marketplace_link_not_found")
    _apply_update(row, body)
    db.commit()
    db.refresh(row)
    return row


def delete_marketplace_link(db: Session, link_id: str) -> None:
    row = db.get(HardwareLockerMarketplaceLink, link_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="marketplace_link_not_found")
    db.delete(row)
    db.commit()


def update_payment_binding(db: Session, binding_id: str, body: HardwareLockerPaymentBindingUpdate) -> HardwareLockerPaymentBinding:
    row = db.get(HardwareLockerPaymentBinding, binding_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="payment_binding_not_found")
    _apply_update(row, body)
    db.commit()
    db.refresh(row)
    return row


def delete_payment_binding(db: Session, binding_id: str) -> None:
    row = db.get(HardwareLockerPaymentBinding, binding_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="payment_binding_not_found")
    db.delete(row)
    db.commit()


def update_carrier_binding(db: Session, binding_id: str, body: HardwareLockerCarrierBindingUpdate) -> HardwareLockerCarrierBinding:
    row = db.get(HardwareLockerCarrierBinding, binding_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="carrier_binding_not_found")
    _apply_update(row, body)
    db.commit()
    db.refresh(row)
    return row


def delete_carrier_binding(db: Session, binding_id: str) -> None:
    row = db.get(HardwareLockerCarrierBinding, binding_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="carrier_binding_not_found")
    db.delete(row)
    db.commit()


def update_domain_reference(db: Session, ref_id: str, body: HardwareDomainReferenceUpdate) -> HardwareDomainReference:
    row = db.get(HardwareDomainReference, ref_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="domain_reference_not_found")
    _apply_update(row, body)
    db.commit()
    db.refresh(row)
    return row


def delete_domain_reference(db: Session, ref_id: str) -> None:
    row = db.get(HardwareDomainReference, ref_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="domain_reference_not_found")
    db.delete(row)
    db.commit()


def get_dashboard(db: Session) -> HardwareCrossDomainDashboardOut:
    sync_pending = (
        db.query(HardwareSyncQueue).filter(HardwareSyncQueue.status.in_(["PENDING", "RETRY"])).count()
    )
    return HardwareCrossDomainDashboardOut(
        vendors=db.query(HardwareVendorPartner).count(),
        operators=db.query(LockerOperator).count(),
        runtime_lockers=db.query(RuntimeLocker).count(),
        assets=db.query(HardwareAsset).count(),
        ecosystem_players=db.query(HardwareEcosystemPlayer).count(),
        marketplace_links=db.query(HardwareLockerMarketplaceLink).count(),
        payment_bindings=db.query(HardwareLockerPaymentBinding).count(),
        carrier_bindings=db.query(HardwareLockerCarrierBinding).count(),
        domain_references=db.query(HardwareDomainReference).count(),
        capex_records=db.query(HardwareLockerCapex).count(),
        opex_records=db.query(HardwareLockerOpex).count(),
        locker_features=db.query(HardwareLockerFeature).count(),
        locker_slots=db.query(HardwareLockerSlot).count(),
        devices=db.query(HardwareDeviceRegistry).count(),
        sync_pending=sync_pending,
        telemetry_24h=db.query(HardwareTelemetryEvent).count(),
    )
