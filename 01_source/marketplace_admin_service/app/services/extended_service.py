from __future__ import annotations

import copy
import json
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.data.channel_players_catalog import CHANNEL_PLAYERS_CATALOG

from app.models.marketplace import MarketplaceCommission, MarketplaceSeller, SellerProduct, SellerReview
from app.models.marketplace_extended import (
    MarketplaceCategory,
    MarketplaceChannelCapability,
    MarketplaceChannelPartner,
    SellerCategoryLink,
    SellerChannelListing,
    SellerCommissionDispute,
    SellerContact,
    SellerKycDocument,
    SellerLockerNetworkLink,
    SellerPayoutAccount,
    SellerSettlementBatch,
    SellerSettlementItem,
)
from app.schemas.marketplace_extended import (
    CategoryCreateIn,
    ChannelCapabilityOut,
    ChannelPartnerOut,
    DisputeCreateIn,
    DisputeUpdateIn,
    IntegrationMatrixGroupOut,
    IntegrationMatrixOut,
    KycDocumentCreateIn,
    KycDocumentUpdateIn,
    MarketplaceDashboardOut,
    PayoutAccountCreateIn,
    SellerCategoryLinkCreateIn,
    SellerChannelListingCreateIn,
    SellerContactCreateIn,
    SellerLockerNetworkLinkCreateIn,
    SettlementBatchCreateIn,
    SettlementBatchUpdateIn,
)
from app.services.crypto_util import new_id
from app.services.seller_service import get_seller_or_404


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# --- Categories ---


def list_categories(db: Session, active_only: bool = False) -> list[MarketplaceCategory]:
    q = db.query(MarketplaceCategory)
    if active_only:
        q = q.filter(MarketplaceCategory.active.is_(True))
    return q.order_by(MarketplaceCategory.sort_order, MarketplaceCategory.name).all()


def create_category(db: Session, body: CategoryCreateIn) -> MarketplaceCategory:
    if db.query(MarketplaceCategory).filter(MarketplaceCategory.code == body.code).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="category_code_exists")
    row = MarketplaceCategory(id=new_id(), created_at=_utcnow(), **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def link_seller_category(db: Session, body: SellerCategoryLinkCreateIn) -> SellerCategoryLink:
    get_seller_or_404(db, body.seller_id)
    cat = db.get(MarketplaceCategory, body.category_id)
    if not cat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="category_not_found")
    exists = (
        db.query(SellerCategoryLink)
        .filter(
            SellerCategoryLink.seller_id == body.seller_id,
            SellerCategoryLink.category_id == body.category_id,
        )
        .first()
    )
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="seller_category_exists")
    if body.is_primary:
        db.query(SellerCategoryLink).filter(SellerCategoryLink.seller_id == body.seller_id).update(
            {"is_primary": False}
        )
    row = SellerCategoryLink(id=new_id(), created_at=_utcnow(), **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_seller_category_links(db: Session, seller_id: str | None = None) -> list[SellerCategoryLink]:
    q = db.query(SellerCategoryLink)
    if seller_id:
        q = q.filter(SellerCategoryLink.seller_id == seller_id)
    return q.all()


# --- Contacts ---


def list_contacts(db: Session, seller_id: str | None = None) -> list[SellerContact]:
    q = db.query(SellerContact)
    if seller_id:
        q = q.filter(SellerContact.seller_id == seller_id)
    return q.order_by(SellerContact.is_primary.desc(), SellerContact.name).all()


def create_contact(db: Session, body: SellerContactCreateIn) -> SellerContact:
    get_seller_or_404(db, body.seller_id)
    now = _utcnow()
    if body.is_primary:
        db.query(SellerContact).filter(SellerContact.seller_id == body.seller_id).update({"is_primary": False})
    row = SellerContact(id=new_id(), created_at=now, updated_at=now, **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def delete_contact(db: Session, contact_id: str) -> None:
    row = db.get(SellerContact, contact_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="contact_not_found")
    db.delete(row)
    db.commit()


# --- Payout accounts ---


def list_payout_accounts(db: Session, seller_id: str | None = None) -> list[SellerPayoutAccount]:
    q = db.query(SellerPayoutAccount)
    if seller_id:
        q = q.filter(SellerPayoutAccount.seller_id == seller_id)
    return q.order_by(SellerPayoutAccount.is_default.desc()).all()


def create_payout_account(db: Session, body: PayoutAccountCreateIn) -> SellerPayoutAccount:
    get_seller_or_404(db, body.seller_id)
    now = _utcnow()
    if body.is_default:
        db.query(SellerPayoutAccount).filter(SellerPayoutAccount.seller_id == body.seller_id).update(
            {"is_default": False}
        )
    row = SellerPayoutAccount(id=new_id(), verified=False, created_at=now, updated_at=now, **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def verify_payout_account(db: Session, account_id: str) -> SellerPayoutAccount:
    row = db.get(SellerPayoutAccount, account_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="payout_account_not_found")
    row.verified = True
    row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    return row


# --- Settlements ---


def list_settlement_batches(db: Session, seller_id: str | None = None) -> list[SellerSettlementBatch]:
    q = db.query(SellerSettlementBatch)
    if seller_id:
        q = q.filter(SellerSettlementBatch.seller_id == seller_id)
    return q.order_by(SellerSettlementBatch.created_at.desc()).all()


def list_settlement_items(db: Session, batch_id: str) -> list[SellerSettlementItem]:
    return (
        db.query(SellerSettlementItem)
        .filter(SellerSettlementItem.batch_id == batch_id)
        .order_by(SellerSettlementItem.created_at)
        .all()
    )


def create_settlement_batch(db: Session, body: SettlementBatchCreateIn) -> SellerSettlementBatch:
    get_seller_or_404(db, body.seller_id)
    commissions = (
        db.query(MarketplaceCommission)
        .filter(
            MarketplaceCommission.seller_id == body.seller_id,
            MarketplaceCommission.status == "SETTLED",
        )
        .all()
    )
    already = {
        i.commission_id
        for i in db.query(SellerSettlementItem)
        .join(SellerSettlementBatch, SellerSettlementBatch.id == SellerSettlementItem.batch_id)
        .filter(SellerSettlementBatch.seller_id == body.seller_id)
        .all()
    }
    eligible = [c for c in commissions if c.id not in already]
    if not eligible:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="no_settled_commissions")

    gross = sum(c.net_to_seller_cents for c in eligible)
    net = gross - body.fees_cents
    now = _utcnow()
    batch = SellerSettlementBatch(
        id=new_id(),
        seller_id=body.seller_id,
        period_start=body.period_start,
        period_end=body.period_end,
        commission_count=len(eligible),
        gross_net_cents=gross,
        fees_cents=body.fees_cents,
        net_payout_cents=net,
        status="DRAFT",
        notes=body.notes,
        created_at=now,
        updated_at=now,
    )
    db.add(batch)
    for c in eligible:
        db.add(
            SellerSettlementItem(
                id=new_id(),
                batch_id=batch.id,
                commission_id=c.id,
                order_id=c.order_id,
                net_to_seller_cents=c.net_to_seller_cents,
                created_at=now,
            )
        )
    db.commit()
    db.refresh(batch)
    return batch


def update_settlement_batch(db: Session, batch_id: str, body: SettlementBatchUpdateIn) -> SellerSettlementBatch:
    row = db.get(SellerSettlementBatch, batch_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="settlement_batch_not_found")
    data = body.model_dump(exclude_unset=True)
    if data.get("status") == "PAID" and not row.settled_at:
        row.settled_at = _utcnow()
    for k, v in data.items():
        setattr(row, k, v)
    row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    return row


# --- KYC ---


def list_kyc_documents(db: Session, seller_id: str | None = None) -> list[SellerKycDocument]:
    q = db.query(SellerKycDocument)
    if seller_id:
        q = q.filter(SellerKycDocument.seller_id == seller_id)
    return q.order_by(SellerKycDocument.created_at.desc()).all()


def create_kyc_document(db: Session, body: KycDocumentCreateIn) -> SellerKycDocument:
    get_seller_or_404(db, body.seller_id)
    now = _utcnow()
    row = SellerKycDocument(
        id=new_id(),
        status="PENDING",
        created_at=now,
        updated_at=now,
        **body.model_dump(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_kyc_document(db: Session, doc_id: str, body: KycDocumentUpdateIn) -> SellerKycDocument:
    row = db.get(SellerKycDocument, doc_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="kyc_document_not_found")
    data = body.model_dump(exclude_unset=True)
    if data.get("status") == "APPROVED":
        row.verified_at = _utcnow()
    for k, v in data.items():
        setattr(row, k, v)
    row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    return row


# --- Disputes ---


def list_disputes(db: Session, seller_id: str | None = None, status_filter: str | None = None) -> list[SellerCommissionDispute]:
    q = db.query(SellerCommissionDispute)
    if seller_id:
        q = q.filter(SellerCommissionDispute.seller_id == seller_id)
    if status_filter:
        q = q.filter(SellerCommissionDispute.status == status_filter)
    return q.order_by(SellerCommissionDispute.opened_at.desc()).all()


def create_dispute(db: Session, body: DisputeCreateIn) -> SellerCommissionDispute:
    get_seller_or_404(db, body.seller_id)
    comm = db.get(MarketplaceCommission, body.commission_id)
    if not comm or comm.seller_id != body.seller_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="commission_not_found")
    open_exists = (
        db.query(SellerCommissionDispute)
        .filter(
            SellerCommissionDispute.commission_id == body.commission_id,
            SellerCommissionDispute.status == "OPEN",
        )
        .first()
    )
    if open_exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="dispute_already_open")
    row = SellerCommissionDispute(
        id=new_id(),
        opened_at=_utcnow(),
        created_at=_utcnow(),
        **body.model_dump(),
    )
    comm.status = "DISPUTED"
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def resolve_dispute(db: Session, dispute_id: str, body: DisputeUpdateIn) -> SellerCommissionDispute:
    row = db.get(SellerCommissionDispute, dispute_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="dispute_not_found")
    row.status = body.status
    row.resolution_notes = body.resolution_notes
    row.resolved_at = _utcnow()
    if body.status == "RESOLVED":
        comm = db.get(MarketplaceCommission, row.commission_id)
        if comm:
            comm.status = "SETTLED"
    db.commit()
    db.refresh(row)
    return row


# --- Channel players (locker / marketplace) ---


def _partner_out(db: Session, row: MarketplaceChannelPartner) -> ChannelPartnerOut:
    caps = (
        db.query(MarketplaceChannelCapability)
        .filter(MarketplaceChannelCapability.channel_partner_id == row.id)
        .order_by(MarketplaceChannelCapability.capability_code)
        .all()
    )
    base = ChannelPartnerOut.model_validate(row)
    return base.model_copy(
        update={"capabilities": [ChannelCapabilityOut.model_validate(c) for c in caps]}
    )


def seed_channel_players(db: Session, *, refresh_existing: bool = True) -> dict[str, int]:
    """Sincroniza catalogo completo de players + capacidades de integracao."""
    now = _utcnow()
    inserted = 0
    updated = 0
    capabilities_upserted = 0

    for raw in CHANNEL_PLAYERS_CATALOG:
        spec = copy.deepcopy(raw)
        caps_spec = spec.pop("capabilities", [])
        regions = spec.pop("regions_json", spec.get("regions", []))
        if isinstance(regions, list):
            regions_json = json.dumps(regions)
        else:
            regions_json = regions if isinstance(regions, str) else "[]"

        payload = {
            k: v
            for k, v in spec.items()
            if k not in ("capabilities", "regions")
        }
        payload["regions_json"] = regions_json
        payload.setdefault("integration_type", "REST")
        payload.setdefault("website", None)

        existing = db.get(MarketplaceChannelPartner, payload["id"])
        if not existing:
            db.add(
                MarketplaceChannelPartner(
                    active=True,
                    created_at=now,
                    **payload,
                )
            )
            inserted += 1
            partner_id = payload["id"]
        elif refresh_existing:
            for k, v in payload.items():
                if k != "id":
                    setattr(existing, k, v)
            updated += 1
            partner_id = existing.id
        else:
            partner_id = existing.id

        for cap_code, protocol, direction in caps_spec:
            cap_row = (
                db.query(MarketplaceChannelCapability)
                .filter(
                    MarketplaceChannelCapability.channel_partner_id == partner_id,
                    MarketplaceChannelCapability.capability_code == cap_code,
                )
                .first()
            )
            if cap_row:
                cap_row.protocol = protocol
                cap_row.direction = direction
                cap_row.enabled = True
            else:
                db.add(
                    MarketplaceChannelCapability(
                        id=new_id(),
                        channel_partner_id=partner_id,
                        capability_code=cap_code,
                        protocol=protocol,
                        direction=direction,
                        created_at=now,
                    )
                )
                capabilities_upserted += 1

    db.commit()
    return {"inserted": inserted, "updated": updated, "capabilities": capabilities_upserted}


def get_integration_matrix(db: Session) -> IntegrationMatrixOut:
    rows = list_channel_partners(db)
    by_group: dict[str, list[ChannelPartnerOut]] = {}
    for row in rows:
        partner = _partner_out(db, row)
        by_group.setdefault(partner.parent_group, []).append(partner)
    groups = [
        IntegrationMatrixGroupOut(parent_group=g, partners=p, total=len(p))
        for g, p in sorted(by_group.items())
    ]
    return IntegrationMatrixOut(groups=groups, total_partners=len(rows))


def list_channel_partners(
    db: Session,
    role: str | None = None,
    country: str | None = None,
    lockers_only: bool = False,
    parent_group: str | None = None,
) -> list[MarketplaceChannelPartner]:
    q = db.query(MarketplaceChannelPartner).filter(MarketplaceChannelPartner.active.is_(True))
    if role:
        q = q.filter(MarketplaceChannelPartner.partner_role == role)
    if country:
        q = q.filter(MarketplaceChannelPartner.country == country.upper())
    if lockers_only:
        q = q.filter(MarketplaceChannelPartner.supports_lockers.is_(True))
    if parent_group:
        q = q.filter(MarketplaceChannelPartner.parent_group == parent_group)
    return q.order_by(MarketplaceChannelPartner.sort_order, MarketplaceChannelPartner.name).all()


def get_channel_partner_or_404(db: Session, partner_id: str) -> MarketplaceChannelPartner:
    row = db.get(MarketplaceChannelPartner, partner_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="channel_partner_not_found")
    return row


def list_seller_channel_listings(db: Session, seller_id: str | None = None) -> list[SellerChannelListing]:
    q = db.query(SellerChannelListing)
    if seller_id:
        q = q.filter(SellerChannelListing.seller_id == seller_id)
    return q.order_by(SellerChannelListing.created_at.desc()).all()


def create_seller_channel_listing(db: Session, body: SellerChannelListingCreateIn) -> SellerChannelListing:
    get_seller_or_404(db, body.seller_id)
    get_channel_partner_or_404(db, body.channel_partner_id)
    exists = (
        db.query(SellerChannelListing)
        .filter(
            SellerChannelListing.seller_id == body.seller_id,
            SellerChannelListing.channel_partner_id == body.channel_partner_id,
        )
        .first()
    )
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="seller_channel_listing_exists")
    now = _utcnow()
    row = SellerChannelListing(id=new_id(), created_at=now, updated_at=now, **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_locker_network_links(db: Session, seller_id: str | None = None) -> list[SellerLockerNetworkLink]:
    q = db.query(SellerLockerNetworkLink).filter(SellerLockerNetworkLink.active.is_(True))
    if seller_id:
        q = q.filter(SellerLockerNetworkLink.seller_id == seller_id)
    return q.order_by(SellerLockerNetworkLink.priority).all()


def create_locker_network_link(db: Session, body: SellerLockerNetworkLinkCreateIn) -> SellerLockerNetworkLink:
    get_seller_or_404(db, body.seller_id)
    partner = get_channel_partner_or_404(db, body.channel_partner_id)
    if not partner.supports_lockers:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="channel_partner_not_locker_network",
        )
    exists = (
        db.query(SellerLockerNetworkLink)
        .filter(
            SellerLockerNetworkLink.seller_id == body.seller_id,
            SellerLockerNetworkLink.channel_partner_id == body.channel_partner_id,
            SellerLockerNetworkLink.locker_id == body.locker_id,
        )
        .first()
    )
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="locker_network_link_exists")
    row = SellerLockerNetworkLink(id=new_id(), created_at=_utcnow(), **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


# --- Dashboard ---


def get_dashboard(db: Session) -> MarketplaceDashboardOut:
    sellers_q = db.query(MarketplaceSeller).filter(MarketplaceSeller.deleted_at.is_(None))
    sellers_total = sellers_q.count()
    sellers_active = sellers_q.filter(MarketplaceSeller.status == "ACTIVE").count()
    sellers_pending = sellers_q.filter(MarketplaceSeller.status == "PENDING_APPROVAL").count()
    products_active = (
        db.query(SellerProduct)
        .filter(SellerProduct.deleted_at.is_(None), SellerProduct.status == "ACTIVE")
        .count()
    )
    pending = db.query(MarketplaceCommission).filter(MarketplaceCommission.status == "PENDING").all()
    commissions_pending = len(pending)
    commissions_pending_cents = sum(c.commission_amount_cents for c in pending)
    commissions_settled = db.query(MarketplaceCommission).filter(MarketplaceCommission.status == "SETTLED").count()
    open_disputes = db.query(SellerCommissionDispute).filter(SellerCommissionDispute.status == "OPEN").count()
    settlement_batches_draft = (
        db.query(SellerSettlementBatch).filter(SellerSettlementBatch.status == "DRAFT").count()
    )
    kyc_pending = db.query(SellerKycDocument).filter(SellerKycDocument.status == "PENDING").count()
    avg_rating = db.query(func.avg(MarketplaceSeller.seller_rating)).filter(
        MarketplaceSeller.deleted_at.is_(None),
        MarketplaceSeller.status == "ACTIVE",
    ).scalar()
    channel_partners_active = (
        db.query(MarketplaceChannelPartner).filter(MarketplaceChannelPartner.active.is_(True)).count()
    )
    seller_channel_listings = db.query(SellerChannelListing).count()
    locker_network_links = db.query(SellerLockerNetworkLink).filter(SellerLockerNetworkLink.active.is_(True)).count()
    return MarketplaceDashboardOut(
        sellers_total=sellers_total,
        sellers_active=sellers_active,
        sellers_pending_approval=sellers_pending,
        products_active=products_active,
        commissions_pending=commissions_pending,
        commissions_pending_cents=commissions_pending_cents,
        commissions_settled=commissions_settled,
        open_disputes=open_disputes,
        settlement_batches_draft=settlement_batches_draft,
        kyc_pending=kyc_pending,
        avg_seller_rating=float(avg_rating) if avg_rating is not None else None,
        channel_partners_active=channel_partners_active,
        seller_channel_listings=seller_channel_listings,
        locker_network_links=locker_network_links,
    )
