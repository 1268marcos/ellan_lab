from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class BiPlayerSegmentTaxonomy(Base):
    __tablename__ = "bi_player_segment_taxonomy"

    code = Column(String(32), primary_key=True)
    label = Column(String(120), nullable=False)
    description = Column(Text, nullable=True)
    sort_order = Column(Integer, nullable=False, default=100)
    active = Column(Boolean, nullable=False, default=True)


class BiPlayerMarketPresence(Base):
    __tablename__ = "bi_player_market_presence"

    id = Column(String(36), primary_key=True)
    network_player_code = Column(String(48), nullable=False, index=True)
    country_code = Column(String(2), nullable=False)
    region_code = Column(String(20), nullable=True)
    locker_count_est = Column(Integer, nullable=True)
    parcel_volume_est_monthly = Column(BigInteger, nullable=True)
    market_share_pct = Column(Numeric(6, 3), nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class BiDataReadinessSnapshot(Base):
    __tablename__ = "bi_data_readiness_snapshots"

    id = Column(String(36), primary_key=True)
    network_player_code = Column(String(48), nullable=False, unique=True, index=True)
    segment_code = Column(String(32), nullable=False, default="LOCKER_NETWORK")
    score_total = Column(Numeric(5, 2), nullable=False, default=0)
    score_data_quality = Column(Numeric(5, 2), nullable=False, default=0)
    score_mart_freshness = Column(Numeric(5, 2), nullable=False, default=0)
    score_api_coverage = Column(Numeric(5, 2), nullable=False, default=0)
    readiness_band = Column(String(16), nullable=False, default="PLANNED")
    blockers_json = Column(Text, nullable=False, default="[]")
    factors_json = Column(Text, nullable=False, default="{}")
    computed_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class BiMartRefreshJob(Base):
    __tablename__ = "bi_mart_refresh_jobs"

    id = Column(String(36), primary_key=True)
    mart_name = Column(String(64), nullable=False)
    target_schema = Column(String(64), nullable=False, default="analytics_analytics")
    status = Column(String(20), nullable=False, default="PENDING")
    rows_affected = Column(BigInteger, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    triggered_by = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class BiKpiAlertRule(Base):
    __tablename__ = "bi_kpi_alert_rules"

    id = Column(String(36), primary_key=True)
    kpi_code = Column(String(48), nullable=False, index=True)
    comparator = Column(String(8), nullable=False, default="LT")
    threshold_value = Column(Numeric(18, 4), nullable=False)
    severity = Column(String(16), nullable=False, default="WARNING")
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class BiKpiAlertEvent(Base):
    __tablename__ = "bi_kpi_alert_events"

    id = Column(String(36), primary_key=True)
    rule_id = Column(String(36), ForeignKey("bi_kpi_alert_rules.id", ondelete="CASCADE"), nullable=False)
    kpi_code = Column(String(48), nullable=False)
    observed_value = Column(Numeric(18, 4), nullable=False)
    status = Column(String(20), nullable=False, default="OPEN")
    network_player_code = Column(String(48), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    resolved_at = Column(DateTime(timezone=True), nullable=True)


class BiDataLineageEdge(Base):
    __tablename__ = "bi_data_lineage_edges"

    id = Column(String(36), primary_key=True)
    source_object = Column(String(120), nullable=False)
    target_object = Column(String(120), nullable=False)
    transform_type = Column(String(32), nullable=False, default="DBT_MODEL")
    owner_team = Column(String(64), nullable=False, default="data-platform")
    notes = Column(Text, nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class BiExportJob(Base):
    __tablename__ = "bi_export_jobs"

    id = Column(String(36), primary_key=True)
    partner_id = Column(String(36), nullable=True)
    export_format = Column(String(16), nullable=False, default="CSV")
    dataset_code = Column(String(48), nullable=False)
    status = Column(String(20), nullable=False, default="QUEUED")
    file_url = Column(String(500), nullable=True)
    row_count = Column(BigInteger, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)


class BiOpsAuditLog(Base):
    __tablename__ = "bi_ops_audit_log"

    id = Column(String(36), primary_key=True)
    event_type = Column(String(40), nullable=False)
    entity_type = Column(String(32), nullable=False)
    entity_id = Column(String(48), nullable=True)
    summary = Column(String(255), nullable=False)
    payload_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class BiUnifiedDomainLink(Base):
    __tablename__ = "bi_unified_domain_links"

    id = Column(String(36), primary_key=True)
    domain_code = Column(String(24), nullable=False)
    label = Column(String(120), nullable=False)
    admin_route = Column(String(255), nullable=True)
    health_path = Column(String(255), nullable=True)
    sort_order = Column(Integer, nullable=False, default=100)
    active = Column(Boolean, nullable=False, default=True)
