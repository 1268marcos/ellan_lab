import enum
from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey
from datetime import datetime
# from app.models.base import Base

from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base

class AllocationState(str, enum.Enum):
    RESERVED_PENDING_PAYMENT = "RESERVED_PENDING_PAYMENT"
    RESERVED_PAID_PENDING_PICKUP = "RESERVED_PAID_PENDING_PICKUP"
    OPENED_FOR_PICKUP = "OPENED_FOR_PICKUP"
    OUT_OF_STOCK = "OUT_OF_STOCK"

class Allocation(Base):
    __tablename__ = "allocations"
    id = Column(String, primary_key=True)
    order_id = Column(String, ForeignKey("orders.id"), nullable=False)

    slot = Column(Integer, nullable=False)          # 1..24
    state = Column(Enum(AllocationState), nullable=False)

    locked_until = Column(DateTime, nullable=True)  # ONLINE: pickup_deadline
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)