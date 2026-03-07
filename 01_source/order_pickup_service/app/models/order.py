# orders (pedido) - padrão "ledger"
from sqlalchemy import Column, String, Integer, DateTime, Enum, Index
import enum
from datetime import datetime

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

    __table_args__ = (
        Index("idx_orders_picked_up_at", "picked_up_at"),
        Index("idx_orders_status_picked_up", "status", "picked_up_at"),
        Index("idx_orders_totem_picked_up", "totem_id", "picked_up_at"),
    )

    id = Column(String, primary_key=True)

    user_id = Column(String, nullable=True)  # ONLINE obrigatório; KIOSK null
    channel = Column(Enum(OrderChannel), nullable=False)

    region = Column(String, nullable=False)   # "SP" | "PT"
    totem_id = Column(String, nullable=False) # "CACIFO-PT-001"
    sku_id = Column(String, nullable=False)

    amount_cents = Column(Integer, nullable=False)
    status = Column(Enum(OrderStatus), nullable=False, default=OrderStatus.PAYMENT_PENDING)

    gateway_transaction_id = Column(String, nullable=True)
    payment_method = Column(String, nullable=True)  # PIX / CARTAO / MBWAY / NFC / etc.

    paid_at = Column(DateTime, nullable=True)
    pickup_deadline_at = Column(DateTime, nullable=True)  # ONLINE somente
    picked_up_at = Column(DateTime, nullable=True)        # data/hora efetiva da retirada

    guest_session_id = Column(String, nullable=True)      # KIOSK opcional
    receipt_email = Column(String, nullable=True)         # KIOSK pós-pagamento
    receipt_phone = Column(String, nullable=True)
    consent_marketing = Column(Integer, nullable=False, default=0)
    guest_phone = Column(String, nullable=True)
    guest_email = Column(String, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def mark_as_picked_up(self):
        self.status = OrderStatus.PICKED_UP
        self.picked_up_at = datetime.utcnow()

    @property
    def is_picked_up(self):
        return self.status == OrderStatus.PICKED_UP and self.picked_up_at is not None

    @property
    def pickup_delay_minutes(self):
        if self.paid_at and self.picked_up_at:
            delta = self.picked_up_at - self.paid_at
            return int(delta.total_seconds() / 60)
        return None

    @property
    def picked_up_within_deadline(self):
        if self.pickup_deadline_at and self.picked_up_at:
            return self.picked_up_at <= self.pickup_deadline_at
        return None