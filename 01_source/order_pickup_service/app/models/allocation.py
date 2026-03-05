import enum
from datetime import datetime

from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey
from app.core.db import Base


class AllocationState(str, enum.Enum):
    """
    Ciclo de vida da alocação (order_pickup_service).
    Não confundir com door_state do backend (/locker/slots), que representa hardware/estoque do cacifo.

    ONLINE:
      RESERVED_PENDING_PAYMENT -> RESERVED_PAID_PENDING_PICKUP -> OPENED_FOR_PICKUP -> PICKED_UP
      (ou) -> EXPIRED / RELEASED / CANCELLED

    KIOSK:
      RESERVED_PENDING_PAYMENT -> OPENED_FOR_PICKUP -> PICKED_UP
      (ou) -> RELEASED / CANCELLED
    """

    # --- Reserva ---
    RESERVED_PENDING_PAYMENT = "RESERVED_PENDING_PAYMENT"         # reservado, aguardando pagamento (TTL curto)
    RESERVED_PAID_PENDING_PICKUP = "RESERVED_PAID_PENDING_PICKUP" # pago, aguardando retirada (janela 2h)

    # --- Retirada ---
    OPENED_FOR_PICKUP = "OPENED_FOR_PICKUP"                       # porta liberada/aberta para retirada
    PICKED_UP = "PICKED_UP"                                       # retirada concluída (estado final ideal)

    # --- Finalizações / exceções ---
    EXPIRED = "EXPIRED"                                           # passou a janela (2h) sem retirada
    RELEASED = "RELEASED"                                         # rollback (pagamento falhou/timeout/admin)
    CANCELLED = "CANCELLED"                                       # cancelado por suporte/regra

    # --- Operacional / segurança (opcional) ---
    FRAUD_REVIEW = "FRAUD_REVIEW"                                 # antifraude travou o fluxo
    ERROR = "ERROR"                                               # erro interno / quarentena
    MAINTENANCE = "MAINTENANCE"                                   # bloqueado por manutenção

    # --- Compat (se você quiser manter por histórico) ---
    OUT_OF_STOCK = "OUT_OF_STOCK"                                 # (melhor ficar no backend door_state)


class Allocation(Base):
    __tablename__ = "allocations"

    id = Column(String, primary_key=True)  # allocation_id vindo do backend /locker/allocate
    order_id = Column(String, ForeignKey("orders.id"), nullable=False)

    slot = Column(Integer, nullable=False)          # 1..24
    state = Column(Enum(AllocationState), nullable=False, default=AllocationState.RESERVED_PENDING_PAYMENT)

    locked_until = Column(DateTime, nullable=True)  # ONLINE: pickup_deadline
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)