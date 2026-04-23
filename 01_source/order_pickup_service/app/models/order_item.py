# 01_source/order_pickup_service/app/models/order_item.py
# 04/04/2026

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.db import Base


class OrderItem(Base):
    """
    Itens do pedido (multi-SKU).

    Mantém compatibilidade com orders.sku_id (legado),
    mas passa a ser a fonte correta para múltiplos itens.
    """

    __tablename__ = "order_items"

    __table_args__ = (
        Index("ix_order_items_order_id", "order_id"),
        Index("ix_order_items_sku_id", "sku_id"),
        Index("ix_order_items_item_status", "item_status"),
        Index("ix_order_items_order_status", "order_id", "item_status"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)

    # relacionamento com order (STRING no seu caso)
    order_id = Column(String, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)

    # produto
    sku_id = Column(String, nullable=False)
    sku_description = Column(String, nullable=True)
    # NCM (Mercosul) — 8 dígitos; VARCHAR permite zeros à esquerda e evolução de formato
    ncm = Column(String(10), nullable=True)

    # quantidade / valor
    quantity = Column(Integer, nullable=False, default=1)
    unit_amount_cents = Column(Integer, nullable=False)
    total_amount_cents = Column(Integer, nullable=False)
    # unit_price_cents = Column(Integer, nullable=False)
    # total_price_cents = Column(Integer, nullable=False)
    # currency = Column(String, nullable=False, default="BRL")

    # logística física
    slot_preference = Column(Integer, nullable=True)
    slot_size = Column(String(20), nullable=True)

    # status do item
    item_status = Column(String(32), nullable=False, default="PENDING")

    # metadados
    metadata_json = Column(JSONB, nullable=False, default={})

    # timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # relacionamento
    order = relationship("Order", back_populates="items")

    # ===================== MÉTODOS =====================

    def recalc_total(self):
        """Recalcula total com base na quantidade"""
        self.total_amount_cents = self.quantity * self.unit_amount_cents

    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "sku_id": self.sku_id,
            "sku_description": self.sku_description,
            "ncm": self.ncm,
            "quantity": self.quantity,
            "unit_amount_cents": self.unit_amount_cents,
            "total_amount_cents": self.total_amount_cents,
            "slot_preference": self.slot_preference,
            "slot_size": self.slot_size,
            "item_status": self.item_status,
            "metadata": self.metadata_json,
        }