from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.manifest import Manifest


def _utc() -> datetime:
    return datetime.now(timezone.utc)


class Delivery(Base):
    __tablename__ = "deliveries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    manifest_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("manifests.id"), nullable=True)
    tracking: Mapped[str] = mapped_column(String(256), nullable=False, unique=True, index=True)
    eta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    signature: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc, onupdate=_utc)

    manifest: Mapped["Manifest | None"] = relationship("Manifest", back_populates="deliveries")
