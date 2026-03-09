from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Index
from datetime import datetime
import enum

from app.core.db import Base


class PickupStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    REDEEMED = "REDEEMED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class PickupRedeemVia(str, enum.Enum):
    QR = "QR"
    MANUAL = "MANUAL"


class Pickup(Base):
    __tablename__ = "pickups"

    id = Column(String, primary_key=True)  # uuid
    order_id = Column(String, ForeignKey("orders.id"), nullable=False, unique=True)

    region = Column(String, nullable=False)
    status = Column(Enum(PickupStatus), nullable=False, default=PickupStatus.ACTIVE)

    expires_at = Column(DateTime, nullable=False)
    current_token_id = Column(String, nullable=True)

    redeemed_at = Column(DateTime, nullable=True)
    redeemed_via = Column(Enum(PickupRedeemVia), nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_pickups_order_id", "order_id"),
        Index("ix_pickups_status", "status"),
        Index("ix_pickups_expires_at", "expires_at"),
    )