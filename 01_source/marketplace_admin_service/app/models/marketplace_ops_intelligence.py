from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import BigInteger, Boolean, Column, Date, DateTime, Integer, Numeric, String, Text

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SellerHealthSnapshot(Base):
    __tablename__ = "seller_health_snapshots"

    id = Column(String(36), primary_key=True)
    seller_id = Column(String(36), nullable=False, index=True)
    snapshot_date = Column(Date, nullable=False)
    health_score = Column(Numeric(5, 2), nullable=False)
    health_band = Column(String(16), nullable=False)
    coverage_pct = Column(Numeric(5, 2), nullable=False, default=0)
    readiness_avg = Column(Numeric(5, 2), nullable=False, default=0)
    open_incidents = Column(Integer, nullable=False, default=0)
    kyc_status = Column(String(20), nullable=True)
    risk_level = Column(String(16), nullable=True)
    factors_json = Column(Text, nullable=False, default="[]")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class MarketplaceOpsPlaybook(Base):
    __tablename__ = "marketplace_ops_playbooks"

    id = Column(String(36), primary_key=True)
    code = Column(String(48), nullable=False, unique=True)
    name = Column(String(160), nullable=False)
    trigger_type = Column(String(32), nullable=False)
    severity = Column(String(16), nullable=False, default="MEDIUM")
    steps_json = Column(Text, nullable=False)
    owner_team = Column(String(64), nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class SellerChannelQuota(Base):
    __tablename__ = "seller_channel_quotas"

    id = Column(String(36), primary_key=True)
    seller_id = Column(String(36), nullable=False, index=True)
    channel_partner_id = Column(String(36), nullable=False, index=True)
    max_active_skus = Column(Integer, nullable=False, default=1000)
    max_orders_per_day = Column(Integer, nullable=False, default=500)
    max_lockers_linked = Column(Integer, nullable=False, default=50)
    current_skus = Column(Integer, nullable=False, default=0)
    current_orders_today = Column(Integer, nullable=False, default=0)
    quota_status = Column(String(20), nullable=False, default="OK")
    reset_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class SellerCatalogSyncJob(Base):
    __tablename__ = "seller_catalog_sync_jobs"

    id = Column(String(36), primary_key=True)
    seller_id = Column(String(36), nullable=False, index=True)
    channel_partner_id = Column(String(36), nullable=False)
    job_type = Column(String(32), nullable=False)
    status = Column(String(20), nullable=False, default="QUEUED")
    items_total = Column(Integer, nullable=False, default=0)
    items_ok = Column(Integer, nullable=False, default=0)
    items_failed = Column(Integer, nullable=False, default=0)
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    error_summary = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class SellerCrossBorderProfile(Base):
    __tablename__ = "seller_cross_border_profiles"

    id = Column(String(36), primary_key=True)
    seller_id = Column(String(36), nullable=False, index=True)
    corridor_code = Column(String(48), nullable=False)
    customs_scheme = Column(String(32), nullable=False)
    ioss_number = Column(String(64), nullable=True)
    vat_number = Column(String(64), nullable=True)
    eori_number = Column(String(64), nullable=True)
    origin_country = Column(String(2), nullable=False)
    dest_country = Column(String(2), nullable=False)
    status = Column(String(20), nullable=False, default="PENDING")
    verified_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class MarketplacePartnerApiHealth(Base):
    __tablename__ = "marketplace_partner_api_health"

    id = Column(String(36), primary_key=True)
    channel_partner_id = Column(String(36), nullable=False, index=True)
    partner_code = Column(String(48), nullable=False)
    measured_at = Column(DateTime(timezone=True), nullable=False)
    availability_pct = Column(Numeric(5, 2), nullable=False, default=100)
    p95_latency_ms = Column(Integer, nullable=False, default=0)
    error_rate_pct = Column(Numeric(5, 2), nullable=False, default=0)
    rate_limit_hits = Column(Integer, nullable=False, default=0)
    health_status = Column(String(16), nullable=False, default="HEALTHY")
    notes = Column(Text, nullable=True)


class SellerPromotionCampaign(Base):
    __tablename__ = "seller_promotion_campaigns"

    id = Column(String(36), primary_key=True)
    seller_id = Column(String(36), nullable=False, index=True)
    channel_partner_id = Column(String(36), nullable=False)
    campaign_code = Column(String(64), nullable=False)
    name = Column(String(160), nullable=False)
    discount_pct = Column(Numeric(5, 2), nullable=True)
    starts_at = Column(DateTime(timezone=True), nullable=False)
    ends_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(20), nullable=False, default="DRAFT")
    budget_cents = Column(BigInteger, nullable=False, default=0)
    spent_cents = Column(BigInteger, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
