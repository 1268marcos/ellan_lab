from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MlUseCase(Base):
    __tablename__ = "ml_use_cases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    code: Mapped[str] = mapped_column(String(48), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(140), nullable=False)
    domain: Mapped[str] = mapped_column(String(32), nullable=False, default="LOCKER")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner_team: Mapped[str | None] = mapped_column(String(64), nullable=True)
    tier: Mapped[str] = mapped_column(String(20), nullable=False, default="STANDARD")
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class MlModelRegistryEntry(Base):
    __tablename__ = "ml_model_registry"
    __table_args__ = (UniqueConstraint("use_case_id", "model_version", name="uq_ml_registry_use_case_version"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    use_case_id: Mapped[str] = mapped_column(String(36), ForeignKey("ml_use_cases.id", ondelete="CASCADE"), index=True)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    algorithm: Mapped[str] = mapped_column(String(64), nullable=False, default="RandomForest")
    framework: Mapped[str | None] = mapped_column(String(32), nullable=True, default="sklearn")
    artifact_uri: Mapped[str | None] = mapped_column(String(500), nullable=True)
    stage: Mapped[str] = mapped_column(String(20), nullable=False, default="DEV")
    status_note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    registry_metadata_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    promoted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class MlTrainingRun(Base):
    __tablename__ = "ml_training_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    use_case_id: Mapped[str] = mapped_column(String(36), ForeignKey("ml_use_cases.id", ondelete="CASCADE"), index=True)
    run_name: Mapped[str] = mapped_column(String(120), nullable=False)
    model_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="QUEUED")
    triggered_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    dataset_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    hyperparams_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    metrics_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)


class MlFeatureDefinition(Base):
    __tablename__ = "ml_feature_definitions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    use_case_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("ml_use_cases.id", ondelete="SET NULL"), nullable=True, index=True
    )
    feature_name: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    feature_group: Mapped[str] = mapped_column(String(40), nullable=False, default="telemetry")
    data_type: Mapped[str] = mapped_column(String(24), nullable=False, default="float")
    source_table: Mapped[str | None] = mapped_column(String(80), nullable=True)
    freshness_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=24)
    is_nullable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)


class MlDriftReport(Base):
    __tablename__ = "ml_drift_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    use_case_id: Mapped[str] = mapped_column(String(36), ForeignKey("ml_use_cases.id", ondelete="CASCADE"), index=True)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    report_date: Mapped[date] = mapped_column(Date, nullable=False)
    drift_type: Mapped[str] = mapped_column(String(24), nullable=False, default="DATA")
    psi_score: Mapped[float | None] = mapped_column(Numeric(6, 4), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="OK")
    details_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)


class MlInferenceSlo(Base):
    __tablename__ = "ml_inference_slo"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    use_case_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("ml_use_cases.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    p95_latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=500)
    min_availability_pct: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=99.5)
    max_error_rate_pct: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=1.0)
    min_predictions_per_day: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class MlAlertRule(Base):
    __tablename__ = "ml_alert_rules"
    __table_args__ = (UniqueConstraint("use_case_id", "rule_code", name="uq_ml_alert_rule_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    use_case_id: Mapped[str] = mapped_column(String(36), ForeignKey("ml_use_cases.id", ondelete="CASCADE"), index=True)
    rule_code: Mapped[str] = mapped_column(String(48), nullable=False)
    metric: Mapped[str] = mapped_column(String(64), nullable=False)
    operator: Mapped[str] = mapped_column(String(8), nullable=False, default="GT")
    threshold: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, default="WARNING")
    notify_webhook: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)


class MlDeploymentEvent(Base):
    __tablename__ = "ml_deployment_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    use_case_id: Mapped[str] = mapped_column(String(36), ForeignKey("ml_use_cases.id", ondelete="CASCADE"), index=True)
    from_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    to_version: Mapped[str] = mapped_column(String(64), nullable=False)
    event_type: Mapped[str] = mapped_column(String(24), nullable=False, default="PROMOTE")
    actor_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)


class MlPartnerUseCaseGrant(Base):
    __tablename__ = "ml_partner_use_case_grants"

    partner_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("ml_data_partners.id", ondelete="CASCADE"), primary_key=True
    )
    use_case_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("ml_use_cases.id", ondelete="CASCADE"), primary_key=True
    )
    scopes_json: Mapped[str] = mapped_column(Text, nullable=False, default='["ml:predict","ml:read"]')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)
