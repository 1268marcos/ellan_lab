from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Index, String, Text
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class OpsActionAudit(Base):
    __tablename__ = "ops_action_audit"

    __table_args__ = (
        Index("ix_ops_audit_created_at", "created_at"),
        Index("ix_ops_audit_order_id", "order_id"),
        Index("ix_ops_audit_action_result", "action", "result"),
        Index("ix_ops_audit_corr_id", "correlation_id"),
    )

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    result: Mapped[str] = mapped_column(String(20), nullable=False)
    correlation_id: Mapped[str] = mapped_column(String(80), nullable=False)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    role: Mapped[str | None] = mapped_column(String(80), nullable=True)
    order_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    details_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
