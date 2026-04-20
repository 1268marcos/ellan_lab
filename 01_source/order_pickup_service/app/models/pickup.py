# 01_source/order_pickup_service/app/models/pickup.py
# 20/04/2026 - correção formato de datetime 

from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime as _DateTime, Enum, ForeignKey, Index, String, Integer
# from sqlalchemy import DateTime as _DateTime

from app.core.db import Base

# Definir alias para não repetir timezone=True em todo lugar:
TZ = _DateTime(timezone=True)


class PickupStatus(str, enum.Enum):
    """
    Estado macro da retirada.

    ACTIVE:
        Retirada liberada e ainda utilizável.

    REDEEMED:
        Retirada concluída. Sem provas por: sensor ou validação humana.

    EXPIRED:
        Janela operacional expirou sem conclusão.

    CANCELLED:
        Fluxo cancelado por operação, compensação ou inconsistência.

    """
    ACTIVE = "ACTIVE"
    REDEEMED = "REDEEMED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class PickupRedeemVia(str, enum.Enum):
    """
    Canal/meio pelo qual a retirada foi efetivamente consumada.
    """
    QR = "QR"
    MANUAL = "MANUAL"
    KIOSK = "KIOSK"
    SENSOR = "SENSOR"
    OPERATOR = "OPERATOR"


class PickupChannel(str, enum.Enum):
    """
    Canal de origem do pedido/retirada.
    Mantido aqui para facilitar analytics e auditoria sem depender sempre de join.
    """
    ONLINE = "ONLINE"
    KIOSK = "KIOSK"


class PickupLifecycleStage(str, enum.Enum):
    """
    Etapa operacional fina do pickup.
    Útil para sensores, troubleshooting e SLA operacional.
    """
    CREATED = "CREATED"
    READY_FOR_PICKUP = "READY_FOR_PICKUP"
    DOOR_OPENED = "DOOR_OPENED"
    ITEM_REMOVED = "ITEM_REMOVED"
    DOOR_CLOSED = "DOOR_CLOSED"
    COMPLETED = "COMPLETED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class Pickup(Base):
    __tablename__ = "pickups"

    # Identidade
    id = Column(String, primary_key=True)
    order_id = Column(String, ForeignKey("orders.id"), nullable=False, unique=True)

    # Contexto de negócio
    channel = Column(Enum(PickupChannel), nullable=False)
    region = Column(String, nullable=False)

    # Contexto físico/operacional
    locker_id = Column(String, nullable=True)
    machine_id = Column(String, nullable=True)
    # slot = Column(String, nullable=True)
    slot = Column(Integer, nullable=True)
    # Opcional: adicionar constraints para dados válidos
    # slot = Column(Integer, nullable=True, default=None)

    # Contexto SaaS / multi-operador
    operator_id = Column(String, nullable=True)
    tenant_id = Column(String, nullable=True)
    site_id = Column(String, nullable=True)

    # Estado principal
    status = Column(Enum(PickupStatus), nullable=False, default=PickupStatus.ACTIVE)
    lifecycle_stage = Column(
        Enum(PickupLifecycleStage),
        nullable=False,
        default=PickupLifecycleStage.CREATED,
    )

    # Segurança/tokenização
    current_token_id = Column(String, nullable=True)

    # Janelas e tempos de operação
    activated_at = Column(TZ, nullable=False, default=lambda: datetime.now(timezone.utc))
    ready_at = Column(TZ, nullable=True)
    expires_at = Column(TZ, nullable=True)

    # Telemetria física / sensores / operação
    door_opened_at = Column(TZ, nullable=True)
    item_removed_at = Column(TZ, nullable=True)
    door_closed_at = Column(TZ, nullable=True)

    # Conclusão/cancelamento
    redeemed_at = Column(TZ, nullable=True)
    redeemed_via = Column(Enum(PickupRedeemVia), nullable=True)
    expired_at = Column(TZ, nullable=True)
    cancelled_at = Column(TZ, nullable=True)
    cancel_reason = Column(String, nullable=True)

    # Auditoria e troubleshooting
    correlation_id = Column(String, nullable=True)
    source_event_id = Column(String, nullable=True)
    sensor_event_id = Column(String, nullable=True)
    notes = Column(String, nullable=True)

    created_at = Column(TZ, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(TZ, nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("ix_pickups_order_id", "order_id"),
        Index("ix_pickups_status", "status"),
        Index("ix_pickups_channel_status", "channel", "status"),
        Index("ix_pickups_region_status", "region", "status"),
        Index("ix_pickups_locker_status", "locker_id", "status"),
        Index("ix_pickups_machine_status", "machine_id", "status"),
        Index("ix_pickups_slot_status", "slot", "status"),
        Index("ix_pickups_operator_status", "operator_id", "status"),
        Index("ix_pickups_tenant_status", "tenant_id", "status"),
        Index("ix_pickups_site_status", "site_id", "status"),
        Index("ix_pickups_expires_at", "expires_at"),
        Index("ix_pickups_redeemed_at", "redeemed_at"),
        Index("ix_pickups_created_at", "created_at"),
        Index("ix_pickups_lifecycle_stage", "lifecycle_stage"),
    )

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc)

    def mark_ready_for_pickup(self) -> None:
        now = datetime.now(timezone.utc)
        self.status = PickupStatus.ACTIVE
        self.lifecycle_stage = PickupLifecycleStage.READY_FOR_PICKUP
        self.ready_at = self.ready_at or now
        self.cancelled_at = None
        self.cancel_reason = None
        self.expired_at = None
        self.touch()

    def mark_door_opened(self) -> None:
        now = datetime.now(timezone.utc)
        self.lifecycle_stage = PickupLifecycleStage.DOOR_OPENED
        self.door_opened_at = self.door_opened_at or now
        self.touch()

    def mark_item_removed(self) -> None:
        now = datetime.now(timezone.utc)
        self.lifecycle_stage = PickupLifecycleStage.ITEM_REMOVED
        self.item_removed_at = self.item_removed_at or now
        self.touch()

    def mark_door_closed(self) -> None:
        now = datetime.now(timezone.utc)
        self.lifecycle_stage = PickupLifecycleStage.DOOR_CLOSED
        self.door_closed_at = self.door_closed_at or now
        self.touch()

    def mark_redeemed(self, via: PickupRedeemVia) -> None:
        now = datetime.now(timezone.utc)
        self.status = PickupStatus.REDEEMED
        self.lifecycle_stage = PickupLifecycleStage.COMPLETED
        self.redeemed_at = self.redeemed_at or now
        self.redeemed_via = via
        self.current_token_id = None
        self.touch()

    def mark_expired(self) -> None:
        now = datetime.now(timezone.utc)
        self.status = PickupStatus.EXPIRED
        self.lifecycle_stage = PickupLifecycleStage.EXPIRED
        self.expired_at = self.expired_at or now
        self.current_token_id = None
        self.touch()

    def mark_cancelled(self, reason: str | None = None) -> None:
        now = datetime.now(timezone.utc)
        self.status = PickupStatus.CANCELLED
        self.lifecycle_stage = PickupLifecycleStage.CANCELLED
        self.cancelled_at = self.cancelled_at or now
        self.cancel_reason = reason
        self.current_token_id = None
        self.touch()

    @property
    def is_active(self) -> bool:
        return self.status == PickupStatus.ACTIVE

    @property
    def is_completed(self) -> bool:
        return self.status == PickupStatus.REDEEMED

    @property
    def can_generate_token(self) -> bool:
        return self.status == PickupStatus.ACTIVE and self.channel == PickupChannel.ONLINE

    @property
    def is_kiosk_flow(self) -> bool:
        return self.channel == PickupChannel.KIOSK

    @property
    def is_online_flow(self) -> bool:
        return self.channel == PickupChannel.ONLINE