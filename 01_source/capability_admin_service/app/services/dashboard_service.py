from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.capability import (
    CapabilityChannel,
    CapabilityContext,
    CapabilityProfile,
    CapabilityRegion,
    PaymentMethodCatalog,
)
from app.models.geo import CapabilityCountry, CapabilityLockerLocation, CapabilityProvince
from datetime import datetime, timedelta, timezone

from app.models.ecosystem import (
    CapabilityEcosystemPlayer,
    CapabilityEcosystemSegment,
    CapabilityProfileAuditLog,
    CapabilityProfilePlayerBinding,
)
from app.models.integration import CapabilityProfileWebhook
from app.schemas.common import DashboardOut
from app.services.matrix_service import build_matrix


def get_dashboard(db: Session) -> DashboardOut:
    active_profiles = (
        db.query(func.count(CapabilityProfile.id)).filter(CapabilityProfile.is_active.is_(True)).scalar() or 0
    )
    return DashboardOut(
        channels=db.query(func.count(CapabilityChannel.id)).scalar() or 0,
        contexts=db.query(func.count(CapabilityContext.id)).scalar() or 0,
        regions=db.query(func.count(CapabilityRegion.id)).scalar() or 0,
        profiles=db.query(func.count(CapabilityProfile.id)).scalar() or 0,
        active_profiles=active_profiles,
        payment_methods=db.query(func.count(PaymentMethodCatalog.id)).scalar() or 0,
        countries=db.query(func.count(CapabilityCountry.id)).scalar() or 0,
        provinces=db.query(func.count(CapabilityProvince.id)).scalar() or 0,
        locker_locations=db.query(func.count(CapabilityLockerLocation.id)).scalar() or 0,
        webhooks=db.query(func.count(CapabilityProfileWebhook.id)).scalar() or 0,
        ecosystem_segments=db.query(func.count(CapabilityEcosystemSegment.id)).scalar() or 0,
        ecosystem_players=db.query(func.count(CapabilityEcosystemPlayer.id)).scalar() or 0,
        player_bindings=db.query(func.count(CapabilityProfilePlayerBinding.id)).scalar() or 0,
        matrix_coverage_pct=build_matrix(db)["coverage_pct"],
        audit_events_24h=db.query(func.count(CapabilityProfileAuditLog.id))
        .filter(CapabilityProfileAuditLog.created_at >= datetime.now(timezone.utc) - timedelta(hours=24))
        .scalar()
        or 0,
    )
