# credits (50%) - Ledger de crédito
# 01_source/order_pickup_service/app/models/credit.py
import uuid
import enum
from sqlalchemy import Column, String, Integer, Enum
from app.models.base import Base

class CreditStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    USED = "USED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"

class Credit(Base):
    __tablename__ = "credits"

    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=True)      # crédito só online (normalmente user_id existe)
    order_id = Column(String, nullable=False, unique=True)
    amount_cents = Column(Integer, nullable=False)
    status = Column(Enum(CreditStatus), nullable=False)

    @staticmethod
    def new_id() -> str:
        return str(uuid.uuid4())



# Abaixo foi a primeira versão - NAO ELIMINAR 
"""
import enum
from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey, Index
from datetime import datetime
from app.models.base import Base

class CreditStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    USED = "USED"
    REVOKED = "REVOKED"

class Credit(Base):
    __tablename__ = "credits"
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    source_order_id = Column(String, ForeignKey("orders.id"), nullable=False)

    amount_cents = Column(Integer, nullable=False)
    status = Column(Enum(CreditStatus), nullable=False, default=CreditStatus.ACTIVE)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (Index("ix_credits_user_id", "user_id"),)
"""