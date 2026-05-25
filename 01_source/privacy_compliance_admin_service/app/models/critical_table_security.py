from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AppCriticalTableRegistry(Base):
    __tablename__ = "app_critical_table_registry"

    table_name = Column(String(64), primary_key=True)
    schema_name = Column(String(32), nullable=False, default="public")
    rls_enabled = Column(Boolean, nullable=False, default=False)
    enforcement_layer = Column(String(24), nullable=False, default="APPLICATION")
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class AppCriticalTablePolicy(Base):
    __tablename__ = "app_critical_table_policy"

    id = Column(String(36), primary_key=True)
    table_name = Column(String(64), nullable=False, index=True)
    operation = Column(String(16), nullable=False)
    role = Column(String(40), nullable=False)
    scope_type = Column(String(24), nullable=False, default="GLOBAL")
    allowed = Column(Boolean, nullable=False, default=True)
    field_mask_json = Column(Text, nullable=True)
    priority = Column(Integer, nullable=False, default=100)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class AppCriticalTableAccessLog(Base):
    __tablename__ = "app_critical_table_access_log"

    id = Column(String(36), primary_key=True)
    table_name = Column(String(64), nullable=False, index=True)
    operation = Column(String(16), nullable=False)
    actor_id = Column(String(36), nullable=True)
    actor_roles_json = Column(Text, nullable=True)
    target_user_id = Column(String(36), nullable=True)
    row_id = Column(String(36), nullable=True)
    decision = Column(String(16), nullable=False)
    reason = Column(String(128), nullable=True)
    service_name = Column(String(64), nullable=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
