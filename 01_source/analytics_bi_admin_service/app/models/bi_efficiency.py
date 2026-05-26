from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Integer, Numeric, String, Text

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class BiDataQualityCheck(Base):
    __tablename__ = "bi_data_quality_checks"

    id = Column(String(36), primary_key=True)
    check_code = Column(String(48), nullable=False, unique=True, index=True)
    target_object = Column(String(120), nullable=False)
    rule_type = Column(String(32), nullable=False, default="NOT_NULL")
    severity = Column(String(16), nullable=False, default="WARNING")
    last_status = Column(String(16), nullable=False, default="UNKNOWN")
    last_score = Column(Numeric(5, 2), nullable=True)
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    details_json = Column(Text, nullable=False, default="{}")
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class BiScheduledExport(Base):
    __tablename__ = "bi_scheduled_exports"

    id = Column(String(36), primary_key=True)
    schedule_code = Column(String(48), nullable=False, unique=True)
    dataset_code = Column(String(48), nullable=False)
    cron_expr = Column(String(64), nullable=False, default="0 6 * * *")
    export_format = Column(String(16), nullable=False, default="CSV")
    partner_id = Column(String(36), nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    last_status = Column(String(20), nullable=False, default="IDLE")
    next_run_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class BiAnomalySignal(Base):
    __tablename__ = "bi_anomaly_signals"

    id = Column(String(36), primary_key=True)
    signal_type = Column(String(32), nullable=False)
    kpi_code = Column(String(48), nullable=True)
    network_player_code = Column(String(48), nullable=True)
    observed_value = Column(Numeric(18, 4), nullable=True)
    baseline_value = Column(Numeric(18, 4), nullable=True)
    deviation_pct = Column(Numeric(8, 3), nullable=True)
    severity = Column(String(16), nullable=False, default="WARNING")
    status = Column(String(20), nullable=False, default="OPEN")
    summary = Column(String(255), nullable=False)
    detected_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    resolved_at = Column(DateTime(timezone=True), nullable=True)


class BiOpsBookmark(Base):
    __tablename__ = "bi_ops_bookmarks"

    id = Column(String(36), primary_key=True)
    owner_id = Column(String(64), nullable=False, default="ops-default")
    label = Column(String(120), nullable=False)
    route_path = Column(String(255), nullable=False)
    query_json = Column(Text, nullable=False, default="{}")
    pinned = Column(Boolean, nullable=False, default=False)
    sort_order = Column(Integer, nullable=False, default=100)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class BiPipelineSyncCheckpoint(Base):
    __tablename__ = "bi_pipeline_sync_checkpoints"

    id = Column(String(36), primary_key=True)
    pipeline_code = Column(String(48), nullable=False, unique=True)
    source_object = Column(String(120), nullable=False)
    target_object = Column(String(120), nullable=False)
    lag_minutes = Column(Integer, nullable=False, default=0)
    rows_synced = Column(BigInteger, nullable=True)
    status = Column(String(20), nullable=False, default="OK")
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)
