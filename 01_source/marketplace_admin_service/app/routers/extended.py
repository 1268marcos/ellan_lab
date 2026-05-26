from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.marketplace_extended import (
    CategoryCreateIn,
    CategoryListOut,
    CategoryOut,
    ChannelPartnerListOut,
    ChannelPartnerOut,
    IntegrationMatrixOut,
    DisputeCreateIn,
    DisputeListOut,
    DisputeOut,
    DisputeUpdateIn,
    KycDocumentCreateIn,
    KycDocumentListOut,
    KycDocumentOut,
    KycDocumentUpdateIn,
    MarketplaceDashboardOut,
    PayoutAccountCreateIn,
    PayoutAccountListOut,
    PayoutAccountOut,
    SellerCategoryLinkCreateIn,
    SellerCategoryLinkListOut,
    SellerCategoryLinkOut,
    SellerChannelListingCreateIn,
    SellerChannelListingListOut,
    SellerChannelListingOut,
    SellerContactCreateIn,
    SellerContactListOut,
    SellerContactOut,
    SellerLockerNetworkLinkCreateIn,
    SellerLockerNetworkLinkListOut,
    SellerLockerNetworkLinkOut,
    SettlementBatchCreateIn,
    SettlementBatchListOut,
    SettlementBatchOut,
    SettlementBatchUpdateIn,
    SettlementItemListOut,
    SettlementItemOut,
    PriorityWorldPlayersOut,
    PriorityWorldPlayerOut,
    SellerPlayerCoverageOut,
)
from app.services import extended_service
from app.services import seller_player_coverage_service

router = APIRouter(tags=["marketplace-extended"])


@router.get("/dashboard", response_model=MarketplaceDashboardOut)
def dashboard(db: Session = Depends(get_db)) -> MarketplaceDashboardOut:
    return extended_service.get_dashboard(db)


@router.post("/channel-partners/seed-players")
def seed_channel_players(db: Session = Depends(get_db)) -> dict:
    return extended_service.seed_channel_players(db, refresh_existing=True)


@router.get("/channel-partners/integration-matrix", response_model=IntegrationMatrixOut)
def integration_matrix(db: Session = Depends(get_db)) -> IntegrationMatrixOut:
    return extended_service.get_integration_matrix(db)


@router.get("/channel-partners", response_model=ChannelPartnerListOut)
def list_channel_partners(
    role: str | None = Query(None),
    country: str | None = Query(None),
    lockers_only: bool = Query(False),
    parent_group: str | None = Query(None),
    db: Session = Depends(get_db),
) -> ChannelPartnerListOut:
    rows = extended_service.list_channel_partners(
        db, role=role, country=country, lockers_only=lockers_only, parent_group=parent_group
    )
    out = [extended_service._partner_out(db, r) for r in rows]
    return ChannelPartnerListOut(partners=out, total=len(out))


@router.get("/channel-partners/{partner_id}", response_model=ChannelPartnerOut)
def get_channel_partner(partner_id: str, db: Session = Depends(get_db)) -> ChannelPartnerOut:
    row = extended_service.get_channel_partner_or_404(db, partner_id)
    return extended_service._partner_out(db, row)


@router.get("/seller-channel-listings", response_model=SellerChannelListingListOut)
def list_seller_channel_listings(
    seller_id: str | None = Query(None), db: Session = Depends(get_db)
) -> SellerChannelListingListOut:
    rows = extended_service.list_seller_channel_listings(db, seller_id=seller_id)
    out = [SellerChannelListingOut.model_validate(r) for r in rows]
    return SellerChannelListingListOut(listings=out, total=len(out))


@router.post("/seller-channel-listings", response_model=SellerChannelListingOut, status_code=status.HTTP_201_CREATED)
def create_seller_channel_listing(
    body: SellerChannelListingCreateIn, db: Session = Depends(get_db)
) -> SellerChannelListingOut:
    return SellerChannelListingOut.model_validate(extended_service.create_seller_channel_listing(db, body))


@router.get("/seller-locker-network-links", response_model=SellerLockerNetworkLinkListOut)
def list_locker_network_links(
    seller_id: str | None = Query(None), db: Session = Depends(get_db)
) -> SellerLockerNetworkLinkListOut:
    rows = extended_service.list_locker_network_links(db, seller_id=seller_id)
    out = [SellerLockerNetworkLinkOut.model_validate(r) for r in rows]
    return SellerLockerNetworkLinkListOut(links=out, total=len(out))


@router.post("/seller-locker-network-links", response_model=SellerLockerNetworkLinkOut, status_code=status.HTTP_201_CREATED)
def create_locker_network_link(
    body: SellerLockerNetworkLinkCreateIn, db: Session = Depends(get_db)
) -> SellerLockerNetworkLinkOut:
    return SellerLockerNetworkLinkOut.model_validate(extended_service.create_locker_network_link(db, body))


@router.get("/categories", response_model=CategoryListOut)
def list_categories(active_only: bool = Query(False), db: Session = Depends(get_db)) -> CategoryListOut:
    rows = extended_service.list_categories(db, active_only=active_only)
    out = [CategoryOut.model_validate(r) for r in rows]
    return CategoryListOut(categories=out, total=len(out))


@router.post("/categories", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(body: CategoryCreateIn, db: Session = Depends(get_db)) -> CategoryOut:
    return CategoryOut.model_validate(extended_service.create_category(db, body))


@router.get("/seller-category-links", response_model=SellerCategoryLinkListOut)
def list_category_links(
    seller_id: str | None = Query(None), db: Session = Depends(get_db)
) -> SellerCategoryLinkListOut:
    rows = extended_service.list_seller_category_links(db, seller_id=seller_id)
    out = [SellerCategoryLinkOut.model_validate(r) for r in rows]
    return SellerCategoryLinkListOut(links=out, total=len(out))


@router.post("/seller-category-links", response_model=SellerCategoryLinkOut, status_code=status.HTTP_201_CREATED)
def link_category(body: SellerCategoryLinkCreateIn, db: Session = Depends(get_db)) -> SellerCategoryLinkOut:
    return SellerCategoryLinkOut.model_validate(extended_service.link_seller_category(db, body))


@router.get("/seller-contacts", response_model=SellerContactListOut)
def list_contacts(seller_id: str | None = Query(None), db: Session = Depends(get_db)) -> SellerContactListOut:
    rows = extended_service.list_contacts(db, seller_id=seller_id)
    out = [SellerContactOut.model_validate(r) for r in rows]
    return SellerContactListOut(contacts=out, total=len(out))


@router.post("/seller-contacts", response_model=SellerContactOut, status_code=status.HTTP_201_CREATED)
def create_contact(body: SellerContactCreateIn, db: Session = Depends(get_db)) -> SellerContactOut:
    return SellerContactOut.model_validate(extended_service.create_contact(db, body))


@router.delete("/seller-contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact(contact_id: str, db: Session = Depends(get_db)) -> None:
    extended_service.delete_contact(db, contact_id)


@router.get("/seller-payout-accounts", response_model=PayoutAccountListOut)
def list_payout_accounts(
    seller_id: str | None = Query(None), db: Session = Depends(get_db)
) -> PayoutAccountListOut:
    rows = extended_service.list_payout_accounts(db, seller_id=seller_id)
    out = [PayoutAccountOut.model_validate(r) for r in rows]
    return PayoutAccountListOut(accounts=out, total=len(out))


@router.post("/seller-payout-accounts", response_model=PayoutAccountOut, status_code=status.HTTP_201_CREATED)
def create_payout_account(body: PayoutAccountCreateIn, db: Session = Depends(get_db)) -> PayoutAccountOut:
    return PayoutAccountOut.model_validate(extended_service.create_payout_account(db, body))


@router.post("/seller-payout-accounts/{account_id}/verify", response_model=PayoutAccountOut)
def verify_payout_account(account_id: str, db: Session = Depends(get_db)) -> PayoutAccountOut:
    return PayoutAccountOut.model_validate(extended_service.verify_payout_account(db, account_id))


@router.get("/seller-settlement-batches", response_model=SettlementBatchListOut)
def list_settlement_batches(
    seller_id: str | None = Query(None), db: Session = Depends(get_db)
) -> SettlementBatchListOut:
    rows = extended_service.list_settlement_batches(db, seller_id=seller_id)
    out = [SettlementBatchOut.model_validate(r) for r in rows]
    return SettlementBatchListOut(batches=out, total=len(out))


@router.post("/seller-settlement-batches", response_model=SettlementBatchOut, status_code=status.HTTP_201_CREATED)
def create_settlement_batch(body: SettlementBatchCreateIn, db: Session = Depends(get_db)) -> SettlementBatchOut:
    return SettlementBatchOut.model_validate(extended_service.create_settlement_batch(db, body))


@router.patch("/seller-settlement-batches/{batch_id}", response_model=SettlementBatchOut)
def update_settlement_batch(
    batch_id: str, body: SettlementBatchUpdateIn, db: Session = Depends(get_db)
) -> SettlementBatchOut:
    return SettlementBatchOut.model_validate(extended_service.update_settlement_batch(db, batch_id, body))


@router.get("/seller-settlement-batches/{batch_id}/items", response_model=SettlementItemListOut)
def list_settlement_items(batch_id: str, db: Session = Depends(get_db)) -> SettlementItemListOut:
    rows = extended_service.list_settlement_items(db, batch_id)
    out = [SettlementItemOut.model_validate(r) for r in rows]
    return SettlementItemListOut(items=out, total=len(out))


@router.get("/seller-kyc-documents", response_model=KycDocumentListOut)
def list_kyc(seller_id: str | None = Query(None), db: Session = Depends(get_db)) -> KycDocumentListOut:
    rows = extended_service.list_kyc_documents(db, seller_id=seller_id)
    out = [KycDocumentOut.model_validate(r) for r in rows]
    return KycDocumentListOut(documents=out, total=len(out))


@router.post("/seller-kyc-documents", response_model=KycDocumentOut, status_code=status.HTTP_201_CREATED)
def create_kyc(body: KycDocumentCreateIn, db: Session = Depends(get_db)) -> KycDocumentOut:
    return KycDocumentOut.model_validate(extended_service.create_kyc_document(db, body))


@router.patch("/seller-kyc-documents/{doc_id}", response_model=KycDocumentOut)
def update_kyc(doc_id: str, body: KycDocumentUpdateIn, db: Session = Depends(get_db)) -> KycDocumentOut:
    return KycDocumentOut.model_validate(extended_service.update_kyc_document(db, doc_id, body))


@router.get("/seller-commission-disputes", response_model=DisputeListOut)
def list_disputes(
    seller_id: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
) -> DisputeListOut:
    rows = extended_service.list_disputes(db, seller_id=seller_id, status_filter=status_filter)
    out = [DisputeOut.model_validate(r) for r in rows]
    return DisputeListOut(disputes=out, total=len(out))


@router.post("/seller-commission-disputes", response_model=DisputeOut, status_code=status.HTTP_201_CREATED)
def create_dispute(body: DisputeCreateIn, db: Session = Depends(get_db)) -> DisputeOut:
    return DisputeOut.model_validate(extended_service.create_dispute(db, body))


@router.patch("/seller-commission-disputes/{dispute_id}", response_model=DisputeOut)
def resolve_dispute(dispute_id: str, body: DisputeUpdateIn, db: Session = Depends(get_db)) -> DisputeOut:
    return DisputeOut.model_validate(extended_service.resolve_dispute(db, dispute_id, body))


@router.get("/priority-players/world-locker-marketplace", response_model=PriorityWorldPlayersOut)
def world_priority_players(db: Session = Depends(get_db)) -> PriorityWorldPlayersOut:
    rows = seller_player_coverage_service.world_priority_players_catalog(db)
    out = [PriorityWorldPlayerOut.model_validate(r) for r in rows]
    return PriorityWorldPlayersOut(players=out, total=len(out))


@router.get("/priority-players/extended-world", response_model=PriorityWorldPlayersOut)
def extended_world_players(db: Session = Depends(get_db)) -> PriorityWorldPlayersOut:
    rows = seller_player_coverage_service.extended_world_players_catalog(db)
    out = [PriorityWorldPlayerOut.model_validate(r) for r in rows]
    return PriorityWorldPlayersOut(players=out, total=len(out))


@router.post("/priority-players/seed-seller-links")
@router.post("/channel-partners/seed-seller-priority-links")
def seed_priority_seller_links(
    seller_id: str = "mk-seller-demo-001", db: Session = Depends(get_db)
) -> dict:
    return seller_player_coverage_service.seed_priority_player_links(db, seller_id=seller_id)


@router.get("/sellers/{seller_id}/player-coverage", response_model=SellerPlayerCoverageOut)
def get_seller_player_coverage(seller_id: str, db: Session = Depends(get_db)) -> SellerPlayerCoverageOut:
    return SellerPlayerCoverageOut.model_validate(seller_player_coverage_service.seller_player_coverage(db, seller_id))
