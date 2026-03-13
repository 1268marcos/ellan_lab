# 01_source/order_pickup_service/app/models/allocation.py
import enum
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Index, Integer, String

from app.core.db import Base


class AllocationState(str, enum.Enum):
    """
    Ciclo de vida da alocação (order_pickup_service).
    Não confundir com door_state do backend (/locker/slots), que representa hardware/estoque do cacifo.

    ONLINE:
      RESERVED_PENDING_PAYMENT
      -> RESERVED_PAID_PENDING_PICKUP
      -> OPENED_FOR_PICKUP
      -> PICKED_UP
      (ou) -> EXPIRED / RELEASED / CANCELLED

    KIOSK (fase atual):
      RESERVED_PENDING_PAYMENT
      -> OPENED_FOR_PICKUP
      -> PICKED_UP apenas quando houver confirmação explícita de retirada
      (ou) -> RELEASED / CANCELLED

    Observação:
    - OUT_OF_STOCK é preferencialmente um estado do backend regional / hardware.
    - Aqui em order_pickup_service guardamos a semântica de alocação do pedido.
    """

    # --- Reserva ---
    RESERVED_PENDING_PAYMENT = "RESERVED_PENDING_PAYMENT"
    RESERVED_PAID_PENDING_PICKUP = "RESERVED_PAID_PENDING_PICKUP"

    # --- Retirada / liberação ---
    OPENED_FOR_PICKUP = "OPENED_FOR_PICKUP"
    PICKED_UP = "PICKED_UP"

    # --- Finalizações / exceções ---
    EXPIRED = "EXPIRED"
    RELEASED = "RELEASED"
    CANCELLED = "CANCELLED"

    # --- Operacional / segurança (opcional) ---
    FRAUD_REVIEW = "FRAUD_REVIEW"
    ERROR = "ERROR"
    MAINTENANCE = "MAINTENANCE"

    # --- Compat legado / histórico ---
    OUT_OF_STOCK = "OUT_OF_STOCK"


class Allocation(Base):
    __tablename__ = "allocations"

    __table_args__ = (
        Index("idx_allocations_order_id", "order_id"),
        Index("idx_allocations_state", "state"),
        Index("idx_allocations_locker_slot_state", "locker_id", "slot", "state"),
        Index("idx_allocations_created_at", "created_at"),
    )

    id = Column(String, primary_key=True)  # allocation_id vindo do backend /locker/allocate
    order_id = Column(String, ForeignKey("orders.id"), nullable=False)

    locker_id = Column(String, nullable=True)  # espelha o totem_id/order locker operacional
    slot = Column(Integer, nullable=False)  # 1..24
    state = Column(
        Enum(AllocationState),
        nullable=False,
        default=AllocationState.RESERVED_PENDING_PAYMENT,
    )

    # ONLINE: normalmente acompanha pickup_deadline_at
    # KIOSK: tende a ficar None após commit/abertura
    locked_until = Column(DateTime, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    def touch(self) -> None:
        self.updated_at = datetime.utcnow()

    def mark_reserved_pending_payment(self) -> None:
        self.state = AllocationState.RESERVED_PENDING_PAYMENT
        self.touch()

    def mark_reserved_paid_pending_pickup(self) -> None:
        self.state = AllocationState.RESERVED_PAID_PENDING_PICKUP
        self.touch()

    def mark_opened_for_pickup(self) -> None:
        self.state = AllocationState.OPENED_FOR_PICKUP
        self.locked_until = None
        self.touch()

    def mark_picked_up(self) -> None:
        self.state = AllocationState.PICKED_UP
        self.locked_until = None
        self.touch()

    def mark_expired(self) -> None:
        self.state = AllocationState.EXPIRED
        self.locked_until = None
        self.touch()

    def mark_released(self) -> None:
        self.state = AllocationState.RELEASED
        self.locked_until = None
        self.touch()

    def mark_cancelled(self) -> None:
        self.state = AllocationState.CANCELLED
        self.locked_until = None
        self.touch()

    def mark_fraud_review(self) -> None:
        self.state = AllocationState.FRAUD_REVIEW
        self.touch()

    def mark_error(self) -> None:
        self.state = AllocationState.ERROR
        self.touch()

    def mark_maintenance(self) -> None:
        self.state = AllocationState.MAINTENANCE
        self.touch()

    @property
    def is_final_state(self) -> bool:
        return self.state in {
            AllocationState.PICKED_UP,
            AllocationState.EXPIRED,
            AllocationState.RELEASED,
            AllocationState.CANCELLED,
        }