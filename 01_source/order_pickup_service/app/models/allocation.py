import enum
from datetime import datetime

from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey
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
      -> DISPENSE físico em andamento / concluído no hardware
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

    id = Column(String, primary_key=True)  # allocation_id vindo do backend /locker/allocate
    order_id = Column(String, ForeignKey("orders.id"), nullable=False)

    slot = Column(Integer, nullable=False)  # 1..24
    state = Column(Enum(AllocationState), nullable=False, default=AllocationState.RESERVED_PENDING_PAYMENT)

    # ONLINE: normalmente acompanha pickup_deadline_at
    # KIOSK: tende a ficar None após commit/abertura
    locked_until = Column(DateTime, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)