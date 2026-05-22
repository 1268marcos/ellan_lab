from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Float, Integer, Numeric, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MlModelMetadata(Base):
    __tablename__ = "ml_model_metadata"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    trained_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)
    metrics_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACTIVE")


class MlFeaturesDaily(Base):
    __tablename__ = "ml_features_daily"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    locker_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    feature_date: Mapped[date] = mapped_column(Date, nullable=False)
    temperature_mean: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    humidity_mean: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    battery_min: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    door_failures_7d: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    usage_events_7d: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    uptime_hours_7d: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    failure_label_7d: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)


class MlPredictionsLog(Base):
    __tablename__ = "ml_predictions_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    locker_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    predicted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)
    failure_probability: Mapped[float] = mapped_column(Numeric(8, 6), nullable=False)
    health_score: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)


class MlPredictionFeedback(Base):
    __tablename__ = "ml_prediction_feedback"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    prediction_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actual_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    error_pct: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    feedback_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    model_performance_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)
