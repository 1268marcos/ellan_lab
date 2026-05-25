from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

_SRC_ROOT = Path(__file__).resolve().parents[3]
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from shared.integration.capability_bridge import (  # noqa: E402
    HARDWARE_TO_MARKETPLACE_CODE,
    HARDWARE_TO_MARKETPLACE_PARTNER_ID,
    expected_hardware_capabilities,
    marketplace_code_for_hardware,
    score_player_readiness,
)

from app.models.cross_domain import HardwareEcosystemPlayer, HardwareLockerMarketplaceLink
from app.models.integration import (
    HardwareEcosystemPlayerRelation,
    HardwareLockerChannelBinding,
    HardwarePlayerIntegrationCapability,
    HardwarePlayerSegmentCatalog,
)
from app.schemas.integration import (
    HardwareIntegrationHubSummaryOut,
    HardwareIntegrationReadinessOut,
    HardwareMarketplaceBridgeOut,
    HardwareMarketplaceBridgePlayerOut,
)
from app.services.crypto_util import new_id


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def list_segments(db: Session) -> list[HardwarePlayerSegmentCatalog]:
    return db.query(HardwarePlayerSegmentCatalog).order_by(HardwarePlayerSegmentCatalog.sort_order).all()


def list_capabilities(db: Session, player_code: str | None = None) -> list[HardwarePlayerIntegrationCapability]:
    q = db.query(HardwarePlayerIntegrationCapability)
    if player_code:
        q = q.filter(HardwarePlayerIntegrationCapability.player_code == player_code)
    return q.order_by(HardwarePlayerIntegrationCapability.player_code).all()


def list_player_relations(db: Session, player_code: str | None = None) -> list[HardwareEcosystemPlayerRelation]:
    q = db.query(HardwareEcosystemPlayerRelation)
    if player_code:
        q = q.filter(
            (HardwareEcosystemPlayerRelation.from_player_code == player_code)
            | (HardwareEcosystemPlayerRelation.to_player_code == player_code)
        )
    return q.all()


def list_channel_bindings(
    db: Session, locker_id: str | None = None, channel_type: str | None = None
) -> list[HardwareLockerChannelBinding]:
    q = db.query(HardwareLockerChannelBinding)
    if locker_id:
        q = q.filter(HardwareLockerChannelBinding.locker_id == locker_id)
    if channel_type:
        q = q.filter(HardwareLockerChannelBinding.channel_type == channel_type)
    return q.order_by(HardwareLockerChannelBinding.priority).all()


def _player_capability_keys(db: Session, player_id: str) -> set[tuple[str, str]]:
    rows = (
        db.query(HardwarePlayerIntegrationCapability)
        .filter(HardwarePlayerIntegrationCapability.player_id == player_id)
        .all()
    )
    return {(r.capability_code, r.target_domain) for r in rows}


def sync_player_capabilities_mirror(
    db: Session,
    player: dict,
    *,
    refresh_existing: bool = True,
) -> dict[str, int]:
    """Espelho 1:1 com catálogo Python (como marketplace_channel_capabilities)."""
    pid = player["id"]
    pcode = player["player_code"]
    desired = expected_hardware_capabilities(
        player_code=pcode,
        segment=player["segment"],
        parent_group=player["parent_group"],
        integration_mode=player["integration_mode"],
        supports_lockers=player["supports_lockers"],
        supports_marketplace=player["supports_marketplace"],
        supports_food_delivery=player["supports_food_delivery"],
        supports_aggregation=player["supports_aggregation"],
        explicit=list(player.get("capabilities") or []),
    )
    desired_keys = {(c[0], c[3]) for c in desired}
    inserted = updated = removed = 0

    stale = (
        db.query(HardwarePlayerIntegrationCapability)
        .filter(HardwarePlayerIntegrationCapability.player_id == pid)
        .all()
    )
    for row in stale:
        key = (row.capability_code, row.target_domain)
        if key not in desired_keys:
            db.delete(row)
            removed += 1

    for cap_code, protocol, direction, target_domain in desired:
        cap_row = (
            db.query(HardwarePlayerIntegrationCapability)
            .filter(
                HardwarePlayerIntegrationCapability.player_id == pid,
                HardwarePlayerIntegrationCapability.capability_code == cap_code,
                HardwarePlayerIntegrationCapability.target_domain == target_domain,
            )
            .first()
        )
        if cap_row:
            if refresh_existing:
                changed = False
                if cap_row.protocol != protocol:
                    cap_row.protocol = protocol
                    changed = True
                if cap_row.direction != direction:
                    cap_row.direction = direction
                    changed = True
                if not cap_row.is_active:
                    cap_row.is_active = True
                    changed = True
                if changed:
                    updated += 1
            continue
        db.add(
            HardwarePlayerIntegrationCapability(
                id=new_id(),
                player_id=pid,
                player_code=pcode,
                capability_code=cap_code,
                protocol=protocol,
                direction=direction,
                target_domain=target_domain,
            )
        )
        inserted += 1

    return {"inserted": inserted, "updated": updated, "removed": removed}


def sync_capabilities_from_catalog(db: Session, players: list[dict], *, refresh_existing: bool = True) -> dict[str, int]:
    totals = {"inserted": 0, "updated": 0, "removed": 0}
    for player in players:
        stats = sync_player_capabilities_mirror(db, player, refresh_existing=refresh_existing)
        for k in totals:
            totals[k] += stats[k]
    if any(totals.values()):
        db.commit()
    return totals


def compute_marketplace_bridge(db: Session, players: list[dict] | None = None) -> HardwareMarketplaceBridgeOut:
    if players is None:
        from app.data.global_locker_players_catalog import GLOBAL_LOCKER_PLAYERS

        players = GLOBAL_LOCKER_PLAYERS
    catalog_by_code = {p["player_code"]: p for p in players}
    db_players = db.query(HardwareEcosystemPlayer).all()

    linked = 0
    in_sync = 0
    gaps = 0
    items: list[HardwareMarketplaceBridgePlayerOut] = []

    for row in db_players:
        mkt_code = marketplace_code_for_hardware(row.player_code, row.marketplace_channel_code)
        if not mkt_code:
            continue
        linked += 1
        catalog = catalog_by_code.get(row.player_code)
        expected = (
            expected_hardware_capabilities(
                player_code=row.player_code,
                segment=row.segment,
                parent_group=row.parent_group,
                integration_mode=row.integration_mode,
                supports_lockers=row.supports_lockers,
                supports_marketplace=row.supports_marketplace,
                supports_food_delivery=row.supports_food_delivery,
                supports_aggregation=row.supports_aggregation,
                explicit=list(catalog.get("capabilities") or []) if catalog else None,
            )
            if catalog
            else []
        )
        db_keys = _player_capability_keys(db, row.id)
        expected_keys = {(c[0], c[3]) for c in expected}
        missing = sorted({f"{a}:{b}" for a, b in (expected_keys - db_keys)})
        extra = sorted({f"{a}:{b}" for a, b in (db_keys - expected_keys)})
        synced = not missing and not extra and bool(expected_keys)
        if synced:
            in_sync += 1
        elif missing:
            gaps += 1
        items.append(
            HardwareMarketplaceBridgePlayerOut(
                hardware_player_code=row.player_code,
                marketplace_partner_code=mkt_code,
                marketplace_channel_partner_id=HARDWARE_TO_MARKETPLACE_PARTNER_ID.get(row.player_code),
                capabilities_expected=len(expected_keys),
                capabilities_db=len(db_keys),
                in_sync=synced,
                missing_capabilities=missing,
                extra_capabilities=extra,
            )
        )

    return HardwareMarketplaceBridgeOut(
        marketplace_partners_linked=linked,
        capabilities_in_sync=in_sync,
        marketplace_capability_gaps=gaps,
        capabilities_catalog_expected=sum(i.capabilities_expected for i in items),
        capabilities_db_enabled=sum(i.capabilities_db for i in items),
        items=items,
    )


def list_integration_readiness(db: Session, band: str | None = None) -> list[HardwareIntegrationReadinessOut]:
    rows: list[HardwareIntegrationReadinessOut] = []
    for player in db.query(HardwareEcosystemPlayer).order_by(HardwareEcosystemPlayer.player_code).all():
        caps = (
            db.query(HardwarePlayerIntegrationCapability)
            .filter(
                HardwarePlayerIntegrationCapability.player_id == player.id,
                HardwarePlayerIntegrationCapability.is_active.is_(True),
            )
            .all()
        )
        mkt_code = marketplace_code_for_hardware(player.player_code, player.marketplace_channel_code)
        regions = player.regions_json if isinstance(player.regions_json, list) else []
        score_total, score_cap, score_api, score_ops, readiness_band, blockers = score_player_readiness(
            capability_count=len(caps),
            integration_mode=player.integration_mode,
            parent_group=player.parent_group,
            supports_lockers=player.supports_lockers,
            operator_id=player.operator_id,
            regions_count=len(regions),
            marketplace_linked=bool(mkt_code),
        )
        out = HardwareIntegrationReadinessOut(
            player_id=player.id,
            player_code=player.player_code,
            marketplace_partner_code=mkt_code,
            score_total=score_total,
            score_capabilities=score_cap,
            score_api=score_api,
            score_operations=score_ops,
            readiness_band=readiness_band,
            blockers=blockers,
            capability_count=len(caps),
            computed_at=_utcnow(),
        )
        if band and out.readiness_band != band.upper():
            continue
        rows.append(out)
    return rows


def get_integration_hub_summary(db: Session) -> HardwareIntegrationHubSummaryOut:
    bindings = db.query(HardwareLockerChannelBinding).all()
    readiness_rows = list_integration_readiness(db)
    bands: dict[str, int] = {"GO_LIVE": 0, "PILOT": 0, "PLANNED": 0, "BLOCKED": 0}
    total_score = 0.0
    for r in readiness_rows:
        bands[r.readiness_band] = bands.get(r.readiness_band, 0) + 1
        total_score += r.score_total
    avg_score = round(total_score / len(readiness_rows), 2) if readiness_rows else 0.0
    bridge = compute_marketplace_bridge(db)
    try:
        from app.services import professional_ops_service

        pro = professional_ops_service.professional_ops_summary(db)
        open_incidents = pro.open_incidents
        open_alerts = pro.open_readiness_alerts
        certifications = pro.certifications
        corridors = pro.corridors
        onboarding_runs = pro.onboarding_runs_active
    except Exception:
        open_incidents = open_alerts = certifications = corridors = onboarding_runs = 0

    return HardwareIntegrationHubSummaryOut(
        segments=db.query(HardwarePlayerSegmentCatalog).count(),
        ecosystem_players=db.query(HardwareEcosystemPlayer).count(),
        capabilities=db.query(HardwarePlayerIntegrationCapability).count(),
        player_relations=db.query(HardwareEcosystemPlayerRelation).count(),
        locker_channel_bindings=len(bindings),
        food_delivery_bindings=sum(1 for b in bindings if b.channel_type == "FOOD_DELIVERY"),
        aggregator_bindings=sum(1 for b in bindings if b.channel_type == "AGGREGATOR"),
        marketplace_bindings=sum(1 for b in bindings if b.channel_type in {"MARKETPLACE", "COLLECTION_POINT"}),
        readiness_rows=len(readiness_rows),
        avg_score=avg_score,
        bands=bands,
        partners_with_blockers=sum(1 for r in readiness_rows if r.blockers),
        marketplace_partners_linked=bridge.marketplace_partners_linked,
        capabilities_in_sync=bridge.capabilities_in_sync,
        marketplace_capability_gaps=bridge.marketplace_capability_gaps,
        open_incidents=open_incidents,
        open_readiness_alerts=open_alerts,
        certifications=certifications,
        corridors=corridors,
        onboarding_runs_active=onboarding_runs,
    )


def seed_segments(db: Session, segments: list[dict]) -> int:
    count = 0
    for seg in segments:
        if db.get(HardwarePlayerSegmentCatalog, seg["code"]):
            continue
        db.add(HardwarePlayerSegmentCatalog(**seg))
        count += 1
    if count:
        db.commit()
    return count


def seed_player_capabilities_and_relations(db: Session, players: list[dict]) -> tuple[int, int]:
    cap_stats = sync_capabilities_from_catalog(db, players, refresh_existing=True)
    cap_count = cap_stats["inserted"]

    rel_count = 0
    code_to_id = {p.player_code: p.id for p in db.query(HardwareEcosystemPlayer).all()}

    for player in players:
        pid = player["id"]
        pcode = player["player_code"]
        for relation_type, target_code in player.get("relations") or []:
            to_id = code_to_id.get(target_code)
            if not to_id:
                continue
            exists = (
                db.query(HardwareEcosystemPlayerRelation)
                .filter(
                    HardwareEcosystemPlayerRelation.from_player_id == pid,
                    HardwareEcosystemPlayerRelation.to_player_id == to_id,
                    HardwareEcosystemPlayerRelation.relation_type == relation_type,
                )
                .first()
            )
            if exists:
                continue
            db.add(
                HardwareEcosystemPlayerRelation(
                    id=new_id(),
                    from_player_id=pid,
                    from_player_code=pcode,
                    to_player_id=to_id,
                    to_player_code=target_code,
                    relation_type=relation_type,
                )
            )
            rel_count += 1

    if rel_count:
        db.commit()
    return cap_count, rel_count


def mirror_marketplace_channel_partners(db: Session) -> dict[str, int]:
    """GET channel-partners do marketplace_admin e alinha metadata + links locais."""
    import httpx

    from app.core.config import get_settings

    s = get_settings()
    url = f"{s.marketplace_admin_url}/api/v1/marketplace-admin/channel-partners"
    try:
        with httpx.Client(timeout=s.domain_http_timeout_seconds) as client:
            resp = client.get(url)
            resp.raise_for_status()
            payload = resp.json()
    except httpx.HTTPError:
        return {"marketplace_partners": 0, "matched": 0, "updated": 0, "links_created": 0, "error": "unreachable"}

    partners = payload.get("items") if isinstance(payload, dict) else []
    if not isinstance(partners, list):
        partners = []

    by_code: dict[str, dict] = {}
    for p in partners:
        code = str(p.get("code") or "").upper()
        if code:
            by_code[code] = p

    matched = updated = links_created = 0
    demo_locker = "LOCKER-DEMO-01"

    for hw in db.query(HardwareEcosystemPlayer).all():
        mkt_code = str(hw.marketplace_channel_code or hw.player_code or "").upper()
        partner = by_code.get(mkt_code)
        if not partner:
            continue
        matched += 1
        meta = dict(hw.metadata_json or {})
        pid = str(partner.get("id") or "")
        if meta.get("marketplace_channel_partner_id") != pid:
            meta["marketplace_channel_partner_id"] = pid
            meta["marketplace_channel_partner_code"] = partner.get("code")
            meta["mirror_source"] = "MARKETPLACE_CHANNEL_PARTNERS_HTTP"
            hw.metadata_json = meta
            updated += 1

        exists = (
            db.query(HardwareLockerMarketplaceLink)
            .filter(
                HardwareLockerMarketplaceLink.channel_partner_id == pid,
                HardwareLockerMarketplaceLink.locker_id == demo_locker,
            )
            .first()
        )
        if not exists and hw.supports_marketplace:
            db.add(
                HardwareLockerMarketplaceLink(
                    id=new_id(),
                    seller_id="mk-seller-demo-001",
                    seller_name="Demo Seller BR",
                    channel_partner_id=pid,
                    channel_code=str(partner.get("code") or mkt_code),
                    channel_name=str(partner.get("name") or hw.name),
                    locker_id=demo_locker,
                    priority=100 + links_created,
                    active=True,
                )
            )
            links_created += 1

    if updated or links_created:
        db.commit()

    return {
        "marketplace_partners": len(partners),
        "matched": matched,
        "updated": updated,
        "links_created": links_created,
    }
