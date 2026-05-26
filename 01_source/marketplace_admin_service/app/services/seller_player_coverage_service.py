from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.data.extended_world_players import EXTENDED_WORLD_PLAYERS
from app.data.priority_locker_marketplace_players import PRIORITY_WORLD_PLAYERS, PRIORITY_PLAYER_CODES
from app.models.marketplace_extended import (
    MarketplaceChannelPartner,
    SellerChannelListing,
    SellerLockerNetworkLink,
)
from app.models.marketplace_integration import MarketplaceIntegrationReadiness
from app.services.crypto_util import new_id


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def world_priority_players_catalog(db: Session) -> list[dict]:
    """Catálogo fixo enriquecido com estado no DB e prontidão."""
    readiness = {
        r.partner_code: {
            "readiness_band": r.readiness_band,
            "score_total": float(r.score_total),
        }
        for r in db.query(MarketplaceIntegrationReadiness)
        .filter(MarketplaceIntegrationReadiness.partner_code.in_(PRIORITY_PLAYER_CODES))
        .all()
    }
    partners = {
        p.code: p
        for p in db.query(MarketplaceChannelPartner)
        .filter(MarketplaceChannelPartner.code.in_(PRIORITY_PLAYER_CODES))
        .all()
    }
    out: list[dict] = []
    for spec in PRIORITY_WORLD_PLAYERS:
        code = spec["code"]
        partner = partners.get(code)
        rd = readiness.get(code, {})
        out.append(
            {
                **spec,
                "in_catalog": partner is not None,
                "partner_active": bool(partner.active) if partner else False,
                "supports_lockers": bool(partner.supports_lockers) if partner else spec.get("locker_network"),
                "supports_marketplace": bool(partner.supports_marketplace) if partner else spec.get("listing"),
                "readiness_band": rd.get("readiness_band"),
                "score_total": rd.get("score_total"),
            }
        )
    return out


def extended_world_players_catalog(db: Session) -> list[dict]:
    codes = {p["code"] for p in EXTENDED_WORLD_PLAYERS}
    readiness = {
        r.partner_code: {"readiness_band": r.readiness_band, "score_total": float(r.score_total)}
        for r in db.query(MarketplaceIntegrationReadiness)
        .filter(MarketplaceIntegrationReadiness.partner_code.in_(codes))
        .all()
    }
    partners = {
        p.code: p for p in db.query(MarketplaceChannelPartner).filter(MarketplaceChannelPartner.code.in_(codes)).all()
    }
    out: list[dict] = []
    for spec in EXTENDED_WORLD_PLAYERS:
        code = spec["code"]
        partner = partners.get(code)
        rd = readiness.get(code, {})
        out.append(
            {
                **spec,
                "notes": spec.get("notes", ""),
                "in_catalog": partner is not None,
                "partner_active": bool(partner.active) if partner else False,
                "supports_lockers": bool(partner.supports_lockers) if partner else spec.get("locker_network"),
                "supports_marketplace": bool(partner.supports_marketplace) if partner else spec.get("listing"),
                "readiness_band": rd.get("readiness_band"),
                "score_total": rd.get("score_total"),
            }
        )
    return out


def seller_player_coverage(db: Session, seller_id: str) -> dict:
    listings = {
        l.channel_partner_id: l
        for l in db.query(SellerChannelListing).filter(SellerChannelListing.seller_id == seller_id).all()
    }
    networks = {
        n.channel_partner_id: n
        for n in db.query(SellerLockerNetworkLink)
        .filter(SellerLockerNetworkLink.seller_id == seller_id, SellerLockerNetworkLink.active.is_(True))
        .all()
    }
    partners = {p.id: p for p in db.query(MarketplaceChannelPartner).all()}

    rows: list[dict] = []
    for spec in PRIORITY_WORLD_PLAYERS:
        pid = spec["partner_id"]
        partner = partners.get(pid)
        listing = listings.get(pid)
        network = networks.get(pid)
        rows.append(
            {
                "partner_code": spec["code"],
                "partner_id": pid,
                "role": spec["role"],
                "regions": spec["regions"],
                "notes": spec["notes"],
                "has_marketplace_listing": listing is not None,
                "listing_status": listing.listing_status if listing else None,
                "external_store_id": listing.external_store_id if listing else None,
                "has_locker_network": network is not None,
                "locker_id": network.locker_id if network else None,
                "network_priority": network.priority if network else None,
                "partner_active": bool(partner.active) if partner else False,
                "expected_listing": spec["listing"],
                "expected_locker_network": spec["locker_network"],
                "coverage_complete": (
                    (not spec["listing"] or listing is not None)
                    and (not spec["locker_network"] or network is not None)
                ),
            }
        )
    complete = sum(1 for r in rows if r["coverage_complete"])
    return {
        "seller_id": seller_id,
        "priority_players_total": len(rows),
        "coverage_complete_count": complete,
        "coverage_pct": round(100.0 * complete / len(rows), 1) if rows else 0,
        "players": rows,
    }


def seed_priority_player_links(db: Session, seller_id: str = "mk-seller-demo-001") -> dict[str, int]:
    """Vincula seller demo aos 11 players prioritários (listings + redes locker)."""
    now = _utcnow()
    counts = {"listings": 0, "locker_networks": 0}

    listing_specs = [
        ("mk-list-meli", "mcp-meli", "ML-STORE-DEMO-001"),
        ("mk-list-magalu", "mcp-magalu", "MAGALU-STORE-001"),
        ("mk-list-amazon-br", "mcp-amazon-br", "AMZ-BR-SELLER-001"),
        ("mk-list-amazon-es", "mcp-amazon-es", "AMZ-ES-SELLER-001"),
        ("mk-list-worten", "mcp-worten", "WORTEN-PT-STORE-001"),
        ("mk-list-elcorte", "mcp-elcorte", "ELCORTE-ES-STORE-001"),
    ]
    for lid, cpid, store in listing_specs:
        if db.get(SellerChannelListing, lid):
            continue
        db.add(
            SellerChannelListing(
                id=lid,
                seller_id=seller_id,
                channel_partner_id=cpid,
                external_store_id=store,
                listing_status="ACTIVE",
                created_at=now,
                updated_at=now,
            )
        )
        counts["listings"] += 1

    network_specs = [
        ("mk-net-inpost", "mcp-inpost", "LOCKER-DEMO-01", 5),
        ("mk-net-dhl", "mcp-dhl", "LOCKER-DHL-EU-01", 10),
        ("mk-net-dpd", "mcp-dpd", "LOCKER-DPD-PT-01", 15),
        ("mk-net-correios", "mcp-correios", None, 20),
        ("mk-net-ctt", "mcp-ctt", None, 25),
        ("mk-net-magalu-pudo", "mcp-magalu", "PUDO-MAGALU-001", 30),
        ("mk-net-meli-flex", "mcp-meli", "MELI-FLEX-LOCKER-01", 35),
        ("mk-net-amazon-br", "mcp-amazon-br", "AMAZON-HUB-BR-01", 40),
        ("mk-net-amazon-es", "mcp-amazon-es", "AMAZON-HUB-ES-01", 45),
        ("mk-net-worten", "mcp-worten", "WORTEN-PUDO-001", 50),
        ("mk-net-elcorte", "mcp-elcorte", "ECI-COLLECTION-001", 55),
    ]
    for nid, cpid, locker, prio in network_specs:
        if db.query(SellerLockerNetworkLink).filter(SellerLockerNetworkLink.id == nid).first():
            continue
        db.add(
            SellerLockerNetworkLink(
                id=nid,
                seller_id=seller_id,
                channel_partner_id=cpid,
                locker_id=locker,
                priority=prio,
                active=True,
                created_at=now,
            )
        )
        counts["locker_networks"] += 1

    db.commit()
    return counts
