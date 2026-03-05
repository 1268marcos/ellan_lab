# orders (pedido) - padrão "ledger"
from sqlalchemy import Column, String, Integer, DateTime, Enum
# from app.models.base import Base
import enum
from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base

class OrderStatus(str, enum.Enum):
    PAYMENT_PENDING = "PAYMENT_PENDING"
    PAID_PENDING_PICKUP = "PAID_PENDING_PICKUP"
    DISPENSED = "DISPENSED"
    PICKED_UP = "PICKED_UP"
    EXPIRED_CREDIT_50 = "EXPIRED_CREDIT_50"
    EXPIRED = "EXPIRED"

class OrderChannel(str, enum.Enum):
    ONLINE = "ONLINE"
    KIOSK = "KIOSK"

class Order(Base):
    __tablename__ = "orders"
    id = Column(String, primary_key=True)

    user_id = Column(String, nullable=True)  # ONLINE obrigatório; KIOSK null  # guest = null
    channel = Column(Enum(OrderChannel), nullable=False)

    region = Column(String, nullable=False)   # "SP" | "PT"
    totem_id = Column(String, nullable=False) # "CACIFO-PT-001"
    sku_id = Column(String, nullable=False)

    amount_cents = Column(Integer, nullable=False)
    status = Column(Enum(OrderStatus), nullable=False, default=OrderStatus.PAYMENT_PENDING)

    gateway_transaction_id = Column(String, nullable=True)
    paid_at = Column(DateTime, nullable=True)
    pickup_deadline_at = Column(DateTime, nullable=True)  # ONLINE somente

    guest_session_id = Column(String, nullable=True)      # KIOSK opcional
    receipt_email = Column(String, nullable=True)         # KIOSK pós-pagamento
    receipt_phone = Column(String, nullable=True)
    consent_marketing = Column(Integer, nullable=False, default=0)
    guest_phone = Column(String, nullable=True)
    guest_email = Column(String, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
