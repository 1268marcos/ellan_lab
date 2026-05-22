from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.marketplace import MarketplaceCommission, MarketplaceSeller, SellerProduct, SellerReview
from app.models.marketplace_extended import (
    MarketplaceCategory,
    SellerCategoryLink,
    SellerChannelListing,
    SellerContact,
    SellerKycDocument,
    SellerLockerNetworkLink,
    SellerPayoutAccount,
)
from app.services.crypto_util import new_id
from app.services.extended_service import seed_channel_players


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def run_seed(db: Session) -> dict[str, int]:
    counts = {
        "sellers": 0,
        "products": 0,
        "commissions": 0,
        "reviews": 0,
        "categories": 0,
        "category_links": 0,
        "contacts": 0,
        "payout_accounts": 0,
        "kyc_documents": 0,
        "channel_players": 0,
        "channel_listings": 0,
        "locker_network_links": 0,
    }
    now = _utcnow()

    if not db.get(MarketplaceSeller, "mk-seller-demo-001"):
        db.add(
            MarketplaceSeller(
                id="mk-seller-demo-001",
                legal_name="Loja Demo Marketplace Ltda",
                trade_name="Demo Store",
                tax_id="12.345.678/0001-90",
                email="seller.demo@ellanlab.com",
                phone="+5511999990001",
                website="https://demo-store.ellanlab.example",
                status="ACTIVE",
                commission_pct=Decimal("8.50"),
                monthly_fee_cents=9900,
                seller_rating=Decimal("4.20"),
                total_sales_cents=1250000,
                total_orders=42,
                joined_at=now,
                approved_at=now,
                created_at=now,
                updated_at=now,
            )
        )
        counts["sellers"] += 1

    if not db.get(MarketplaceSeller, "mk-seller-demo-002"):
        db.add(
            MarketplaceSeller(
                id="mk-seller-demo-002",
                legal_name="Artesanato Regional ME",
                trade_name="Artesanato BR",
                tax_id="98.765.432/0001-10",
                email="artesanato@ellanlab.com",
                status="PENDING_APPROVAL",
                commission_pct=Decimal("5.00"),
                joined_at=now,
                created_at=now,
                updated_at=now,
            )
        )
        counts["sellers"] += 1

    if not db.query(SellerProduct).filter(SellerProduct.id == "mk-prod-demo-001").first():
        db.add(
            SellerProduct(
                id="mk-prod-demo-001",
                seller_id="mk-seller-demo-001",
                locker_id="LOCKER-DEMO-01",
                product_id="SKU-DEMO-001",
                seller_sku="DEMO-001",
                price_cents=4990,
                quantity=25,
                status="ACTIVE",
                priority=10,
                created_at=now,
                updated_at=now,
            )
        )
        counts["products"] += 1

    if not db.query(MarketplaceCommission).filter(MarketplaceCommission.id == "mk-comm-demo-001").first():
        db.add(
            MarketplaceCommission(
                id="mk-comm-demo-001",
                seller_id="mk-seller-demo-001",
                order_id="ord-demo-mk-001",
                commission_rate_pct=Decimal("8.50"),
                commission_amount_cents=424,
                ellan_fee_cents=200,
                payment_gateway_fee_cents=150,
                net_to_seller_cents=4216,
                status="PENDING",
                created_at=now,
            )
        )
        counts["commissions"] += 1

    if not db.query(SellerReview).filter(SellerReview.id == "mk-review-demo-001").first():
        db.add(
            SellerReview(
                id="mk-review-demo-001",
                seller_id="mk-seller-demo-001",
                order_id="ord-demo-mk-001",
                user_id="usr-demo-001",
                rating=5,
                comment="Entrega rapida e produto conforme.",
                delivery_rating=5,
                product_quality_rating=5,
                verified_purchase=True,
                created_at=now,
            )
        )
        counts["reviews"] += 1

    if not db.get(MarketplaceCommission, "mk-comm-demo-002"):
        db.add(
            MarketplaceCommission(
                id="mk-comm-demo-002",
                seller_id="mk-seller-demo-001",
                order_id="ord-demo-mk-002",
                commission_rate_pct=Decimal("8.50"),
                commission_amount_cents=300,
                ellan_fee_cents=100,
                payment_gateway_fee_cents=80,
                net_to_seller_cents=3120,
                status="SETTLED",
                settled_at=now,
                created_at=now,
            )
        )
        counts["commissions"] += 1

    categories_seed = [
        ("mk-cat-food", "FOOD", "Alimentos e bebidas", None, 10),
        ("mk-cat-beauty", "BEAUTY", "Beleza e cuidados", None, 20),
        ("mk-cat-tech", "TECH", "Eletronicos", None, 30),
    ]
    for cid, code, name, parent, sort in categories_seed:
        if not db.get(MarketplaceCategory, cid):
            db.add(
                MarketplaceCategory(
                    id=cid,
                    code=code,
                    name=name,
                    parent_id=parent,
                    active=True,
                    sort_order=sort,
                    created_at=now,
                )
            )
            counts["categories"] += 1

    if not db.query(SellerCategoryLink).filter(SellerCategoryLink.id == "mk-scl-demo-001").first():
        db.add(
            SellerCategoryLink(
                id="mk-scl-demo-001",
                seller_id="mk-seller-demo-001",
                category_id="mk-cat-food",
                is_primary=True,
                created_at=now,
            )
        )
        counts["category_links"] += 1

    if not db.query(SellerContact).filter(SellerContact.id == "mk-contact-demo-001").first():
        db.add(
            SellerContact(
                id="mk-contact-demo-001",
                seller_id="mk-seller-demo-001",
                contact_type="PRIMARY",
                name="Maria Comercial",
                email="maria.comercial@demo-store.example",
                phone="+5511988880001",
                is_primary=True,
                created_at=now,
                updated_at=now,
            )
        )
        counts["contacts"] += 1

    if not db.query(SellerPayoutAccount).filter(SellerPayoutAccount.id == "mk-payout-demo-001").first():
        db.add(
            SellerPayoutAccount(
                id="mk-payout-demo-001",
                seller_id="mk-seller-demo-001",
                account_type="PIX",
                label="Conta principal",
                pix_key="seller.demo@pix.example",
                holder_name="Loja Demo Marketplace Ltda",
                holder_tax_id="12.345.678/0001-90",
                is_default=True,
                verified=True,
                created_at=now,
                updated_at=now,
            )
        )
        counts["payout_accounts"] += 1

    if not db.query(SellerKycDocument).filter(SellerKycDocument.id == "mk-kyc-demo-001").first():
        db.add(
            SellerKycDocument(
                id="mk-kyc-demo-001",
                seller_id="mk-seller-demo-001",
                doc_type="CNPJ_CARD",
                status="APPROVED",
                file_ref="s3://ellanlab-demo/kyc/mk-seller-demo-001-cnpj.pdf",
                verified_at=now,
                created_at=now,
                updated_at=now,
            )
        )
        counts["kyc_documents"] += 1

    if not db.query(SellerKycDocument).filter(SellerKycDocument.id == "mk-kyc-demo-002").first():
        db.add(
            SellerKycDocument(
                id="mk-kyc-demo-002",
                seller_id="mk-seller-demo-002",
                doc_type="CNPJ_CARD",
                status="PENDING",
                file_ref="s3://ellanlab-demo/kyc/mk-seller-demo-002-cnpj.pdf",
                created_at=now,
                updated_at=now,
            )
        )
        counts["kyc_documents"] += 1

    cp_sync = seed_channel_players(db)
    counts["channel_players"] = cp_sync.get("inserted", 0) + cp_sync.get("updated", 0)

    listings_seed = [
        ("mk-list-meli", "mk-seller-demo-001", "mcp-meli", "ML-STORE-DEMO-001"),
        ("mk-list-magalu", "mk-seller-demo-001", "mcp-magalu", "MAGALU-STORE-001"),
        ("mk-list-amazon", "mk-seller-demo-001", "mcp-amazon-br", "AMZ-BR-SELLER-001"),
    ]
    for lid, sid, cpid, store in listings_seed:
        if not db.get(SellerChannelListing, lid):
            db.add(
                SellerChannelListing(
                    id=lid,
                    seller_id=sid,
                    channel_partner_id=cpid,
                    external_store_id=store,
                    listing_status="ACTIVE",
                    created_at=now,
                    updated_at=now,
                )
            )
            counts["channel_listings"] += 1

    network_seed = [
        ("mk-net-inpost", "mk-seller-demo-001", "mcp-inpost", "LOCKER-DEMO-01", 10),
        ("mk-net-correios", "mk-seller-demo-001", "mcp-correios", None, 20),
        ("mk-net-ctt", "mk-seller-demo-001", "mcp-ctt", None, 30),
    ]
    for nid, sid, cpid, locker, prio in network_seed:
        if not db.query(SellerLockerNetworkLink).filter(SellerLockerNetworkLink.id == nid).first():
            db.add(
                SellerLockerNetworkLink(
                    id=nid,
                    seller_id=sid,
                    channel_partner_id=cpid,
                    locker_id=locker,
                    priority=prio,
                    active=True,
                    created_at=now,
                )
            )
            counts["locker_network_links"] += 1

    db.commit()
    return counts
