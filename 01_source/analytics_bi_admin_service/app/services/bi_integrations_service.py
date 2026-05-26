from __future__ import annotations

from sqlalchemy.orm import Session

from app.data.player_integrations_catalog import (
    CAPABILITY_LINKS,
    CROSS_DOMAIN_INTEGRATIONS,
    INTEGRATION_PROFILES,
)
from app.models.bi_integrations import (
    BiCrossDomainIntegration,
    BiPlayerCapabilityLink,
    BiPlayerIntegrationProfile,
)
from app.services.crypto_util import new_id


def seed_integrations(db: Session) -> dict[str, int]:
    counts = {"profiles": 0, "capabilities": 0, "cross_domain": 0}
    for row in INTEGRATION_PROFILES:
        code, segment, mode, api_url, auth, webhook, bi_feed, ml, target, docs, status = row
        existing = (
            db.query(BiPlayerIntegrationProfile).filter(BiPlayerIntegrationProfile.network_player_code == code).first()
        )
        if existing:
            existing.segment_code = segment
            existing.integration_mode = mode
            existing.api_base_url = api_url
            existing.auth_method = auth
            existing.webhook_support = webhook
            existing.bi_data_feed = bi_feed
            existing.ml_scoring_enabled = ml
            existing.target_service = target
            existing.docs_url = docs
            existing.status = status
            continue
        db.add(
            BiPlayerIntegrationProfile(
                id=new_id(),
                network_player_code=code,
                segment_code=segment,
                integration_mode=mode,
                api_base_url=api_url,
                auth_method=auth,
                webhook_support=webhook,
                bi_data_feed=bi_feed,
                ml_scoring_enabled=ml,
                target_service=target,
                docs_url=docs,
                status=status,
            )
        )
        counts["profiles"] += 1
    for code, cap, name, proto, direction, ready in CAPABILITY_LINKS:
        if (
            db.query(BiPlayerCapabilityLink)
            .filter(
                BiPlayerCapabilityLink.network_player_code == code,
                BiPlayerCapabilityLink.capability_code == cap,
            )
            .first()
        ):
            continue
        db.add(
            BiPlayerCapabilityLink(
                id=new_id(),
                network_player_code=code,
                capability_code=cap,
                capability_name=name,
                protocol=proto,
                direction=direction,
                production_ready=ready,
            )
        )
        counts["capabilities"] += 1
    for src, domain, tgt, itype, route in CROSS_DOMAIN_INTEGRATIONS:
        if (
            db.query(BiCrossDomainIntegration)
            .filter(
                BiCrossDomainIntegration.source_player_code == src,
                BiCrossDomainIntegration.target_domain == domain,
                BiCrossDomainIntegration.integration_type == itype,
            )
            .first()
        ):
            continue
        db.add(
            BiCrossDomainIntegration(
                id=new_id(),
                source_player_code=src,
                target_domain=domain,
                target_player_code=tgt,
                integration_type=itype,
                route_path=route,
            )
        )
        counts["cross_domain"] += 1
    db.commit()
    return counts


def list_profiles(db: Session, segment: str | None = None) -> list[BiPlayerIntegrationProfile]:
    q = db.query(BiPlayerIntegrationProfile).filter(BiPlayerIntegrationProfile.active.is_(True))
    if segment:
        q = q.filter(BiPlayerIntegrationProfile.segment_code == segment)
    return q.order_by(BiPlayerIntegrationProfile.network_player_code).all()


def list_capabilities(db: Session, player_code: str | None = None) -> list[BiPlayerCapabilityLink]:
    q = db.query(BiPlayerCapabilityLink)
    if player_code:
        q = q.filter(BiPlayerCapabilityLink.network_player_code == player_code)
    return q.order_by(BiPlayerCapabilityLink.network_player_code).all()


def list_cross_domain(db: Session) -> list[BiCrossDomainIntegration]:
    return (
        db.query(BiCrossDomainIntegration)
        .filter(BiCrossDomainIntegration.active.is_(True))
        .order_by(BiCrossDomainIntegration.source_player_code)
        .all()
    )


def integration_matrix(db: Session) -> dict:
    profiles = list_profiles(db)
    by_segment: dict[str, int] = {}
    by_status: dict[str, int] = {}
    ml_enabled = 0
    for p in profiles:
        by_segment[p.segment_code] = by_segment.get(p.segment_code, 0) + 1
        by_status[p.status] = by_status.get(p.status, 0) + 1
        if p.ml_scoring_enabled:
            ml_enabled += 1
    return {
        "profiles": len(profiles),
        "capabilities": db.query(BiPlayerCapabilityLink).count(),
        "cross_domain": db.query(BiCrossDomainIntegration).filter(BiCrossDomainIntegration.active.is_(True)).count(),
        "by_segment": by_segment,
        "by_status": by_status,
        "ml_scoring_enabled": ml_enabled,
    }
