# 01_source/order_pickup_service/app/models/order.py
# orders (pedido) - padrão "ledger"
import enum
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, Index, String, Integer

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


class PaymentMethod(str, enum.Enum):
    PIX = "PIX"
    CARTAO = "CARTAO"
    MBWAY = "MBWAY"
    MULTIBANCO_REFERENCE = "MULTIBANCO_REFERENCE"
    NFC = "NFC"
    APPLE_PAY = "APPLE_PAY"
    GOOGLE_PAY = "GOOGLE_PAY"
    MERCADO_PAGO_WALLET = "MERCADO_PAGO_WALLET"


class CardType(str, enum.Enum):
    CREDIT = "creditCard"
    DEBIT = "debitCard"


class PaymentStatus(str, enum.Enum):
    CREATED = "CREATED"
    PENDING_CUSTOMER_ACTION = "PENDING_CUSTOMER_ACTION"
    PENDING_PROVIDER_CONFIRMATION = "PENDING_PROVIDER_CONFIRMATION"
    APPROVED = "APPROVED"
    DECLINED = "DECLINED"
    EXPIRED = "EXPIRED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    AWAITING_INTEGRATION = "AWAITING_INTEGRATION"


class Order(Base):
    __tablename__ = "orders"

    __table_args__ = (
        Index("idx_orders_status", "status"),
        Index("idx_orders_channel_status", "channel", "status"),
        Index("idx_orders_region_status", "region", "status"),
        Index("idx_orders_region_totem_status", "region", "totem_id", "status"),
        Index("idx_orders_region_totem_created_at", "region", "totem_id", "created_at"),
        Index("idx_orders_paid_at", "paid_at"),
        Index("idx_orders_picked_up_at", "picked_up_at"),
        Index("idx_orders_status_picked_up", "status", "picked_up_at"),
        Index("idx_orders_totem_picked_up", "totem_id", "picked_up_at"),
        Index("idx_orders_public_access_token_hash", "public_access_token_hash"),
    )

    id = Column(String, primary_key=True)

    # ONLINE autenticado pode preencher; guest/KIOSK podem deixar null
    user_id = Column(String, nullable=True)

    channel = Column(Enum(OrderChannel), nullable=False)

    region = Column(String, nullable=False)
    totem_id = Column(String, nullable=False)
    sku_id = Column(String, nullable=False)

    amount_cents = Column(Integer, nullable=False)
    status = Column(Enum(OrderStatus), nullable=False, default=OrderStatus.PAYMENT_PENDING)

    gateway_transaction_id = Column(String, nullable=True)

    payment_method = Column(Enum(PaymentMethod), nullable=True)
    payment_status = Column(
        Enum(PaymentStatus),
        nullable=False,
        default=PaymentStatus.CREATED,
    )
    card_type = Column(Enum(CardType), nullable=True)
    payment_updated_at = Column(DateTime, nullable=True)

    paid_at = Column(DateTime, nullable=True)
    pickup_deadline_at = Column(DateTime, nullable=True)
    picked_up_at = Column(DateTime, nullable=True)

    guest_session_id = Column(String, nullable=True)
    public_access_token_hash = Column(String, nullable=True)

    receipt_email = Column(String, nullable=True)
    receipt_phone = Column(String, nullable=True)
    consent_marketing = Column(Integer, nullable=False, default=0)
    guest_phone = Column(String, nullable=True)
    guest_email = Column(String, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    def touch(self) -> None:
        self.updated_at = datetime.utcnow()

    def mark_payment_pending_customer_action(self) -> None:
        self.payment_status = PaymentStatus.PENDING_CUSTOMER_ACTION
        self.payment_updated_at = datetime.utcnow()
        self.touch()

    def mark_payment_pending_provider_confirmation(self) -> None:
        self.payment_status = PaymentStatus.PENDING_PROVIDER_CONFIRMATION
        self.payment_updated_at = datetime.utcnow()
        self.touch()

    def mark_payment_approved(self) -> None:
        self.payment_status = PaymentStatus.APPROVED
        self.payment_updated_at = datetime.utcnow()
        self.paid_at = self.paid_at or datetime.utcnow()
        self.touch()

    def mark_payment_declined(self) -> None:
        self.payment_status = PaymentStatus.DECLINED
        self.payment_updated_at = datetime.utcnow()
        self.touch()

    def mark_payment_expired(self) -> None:
        self.payment_status = PaymentStatus.EXPIRED
        self.payment_updated_at = datetime.utcnow()
        self.touch()

    def mark_payment_failed(self) -> None:
        self.payment_status = PaymentStatus.FAILED
        self.payment_updated_at = datetime.utcnow()
        self.touch()

    def mark_payment_cancelled(self) -> None:
        self.payment_status = PaymentStatus.CANCELLED
        self.payment_updated_at = datetime.utcnow()
        self.touch()

    def mark_payment_awaiting_integration(self) -> None:
        self.payment_status = PaymentStatus.AWAITING_INTEGRATION
        self.payment_updated_at = datetime.utcnow()
        self.touch()

    def mark_as_picked_up(self) -> None:
        self.status = OrderStatus.PICKED_UP
        self.picked_up_at = datetime.utcnow()
        self.touch()

    @property
    def is_picked_up(self) -> bool:
        return self.status == OrderStatus.PICKED_UP and self.picked_up_at is not None

    @property
    def pickup_delay_minutes(self) -> int | None:
        if self.paid_at and self.picked_up_at:
            delta = self.picked_up_at - self.paid_at
            return int(delta.total_seconds() / 60)
        return None

    @property
    def picked_up_within_deadline(self) -> bool | None:
        if self.pickup_deadline_at and self.picked_up_at:
            return self.picked_up_at <= self.pickup_deadline_at
        return None