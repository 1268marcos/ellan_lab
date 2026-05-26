from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import inspect, text
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
from app.models.webhook import SellerWebhookEndpoint
from app.services.crypto_util import hash_secret
from app.services.crypto_util import new_id
from app.services import integration_readiness_service
from app.services.extended_service import seed_channel_players


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _table_has_row(db: Session, table: str, column: str, value: str) -> bool:
    """Evita FK violation no Postgres central; em SQLite de teste tabelas podem faltar."""
    bind = db.get_bind()
    tables = set(inspect(bind).get_table_names())
    if table not in tables:
        return bind.dialect.name == "sqlite"
    row = db.execute(
        text(f"SELECT 1 FROM {table} WHERE {column} = :v LIMIT 1"),
        {"v": value},
    ).first()
    return row is not None


def _order_exists(db: Session, order_id: str) -> bool:
    return _table_has_row(db, "orders", "id", order_id)


def _locker_exists(db: Session, locker_id: str) -> bool:
    return _table_has_row(db, "lockers", "id", locker_id)


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
        "channel_capabilities": 0,
        "integration_readiness": 0,
        "integration_incidents": 0,
        "channel_listings": 0,
        "locker_network_links": 0,
        "settlement_batches": 0,
        "settlement_items": 0,
        "disputes": 0,
        "seller_webhooks": 0,
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

    if (
        _locker_exists(db, "LOCKER-DEMO-01")
        and not db.query(SellerProduct).filter(SellerProduct.id == "mk-prod-demo-001").first()
    ):
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

    if (
        _order_exists(db, "ord-demo-mk-001")
        and not db.query(MarketplaceCommission).filter(MarketplaceCommission.id == "mk-comm-demo-001").first()
    ):
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

    if (
        _order_exists(db, "ord-demo-mk-001")
        and not db.query(SellerReview).filter(SellerReview.id == "mk-review-demo-001").first()
    ):
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

    if _order_exists(db, "ord-demo-mk-002") and not db.get(MarketplaceCommission, "mk-comm-demo-002"):
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
    counts["channel_capabilities"] = cp_sync.get("capabilities_db_enabled", 0)
    counts["integration_readiness"] = cp_sync.get("readiness_upserted", 0)
    counts["integration_incidents"] = integration_readiness_service.seed_demo_incidents(db)
    from app.services import readiness_alert_service

    counts["capability_webhooks"] = readiness_alert_service.seed_demo_capability_webhooks(db)

    from app.services import player_ecosystem_service
    from app.services import seller_player_coverage_service

    eco = player_ecosystem_service.seed_player_ecosystem(db)
    counts["player_ecosystem"] = sum(eco.values())

    from app.services import ops_intelligence_service

    ops = ops_intelligence_service.seed_ops_intelligence(db)
    counts["ops_intelligence"] = sum(ops.values())

    from app.services import seller_operations_service

    sop = seller_operations_service.seed_seller_operations(db)
    counts["seller_operations"] = sum(sop.values())

    link_counts = seller_player_coverage_service.seed_priority_player_links(db, "mk-seller-demo-001")
    counts["channel_listings"] += link_counts.get("listings", 0)
    counts["locker_network_links"] += link_counts.get("locker_networks", 0)

    if not db.get(SellerWebhookEndpoint, "mk-wh-demo-001"):
        secret = "whsec_mk_seller_demo"
        db.add(
            SellerWebhookEndpoint(
                id="mk-wh-demo-001",
                seller_id="mk-seller-demo-001",
                url="https://demo-store.ellanlab.example/hooks/marketplace",
                secret_hash=hash_secret(secret),
                secret_key=secret,
                events_json='["order.created","commission.settled"]',
                api_version="v1",
                active=True,
                created_at=now,
                updated_at=now,
            )
        )
        counts["seller_webhooks"] += 1

    from app.services import seller_professional_service

    prof = seller_professional_service.seed_seller_professional_demo(db)
    counts["seller_professional"] = sum(prof.values())
    seller_professional_service.seed_tier_definitions(db)

    db.commit()
    return counts
