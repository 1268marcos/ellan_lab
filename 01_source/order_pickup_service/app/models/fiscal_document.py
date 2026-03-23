# 01_source/order_pickup_service/app/models/fiscal_document.py
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, Index, Integer, String, Text
from sqlalchemy.dialects.sqlite import JSON

from app.core.db import Base


class FiscalDocument(Base):
    __tablename__ = "fiscal_documents"

    __table_args__ = (
        Index("idx_fiscal_order_id", "order_id"),
        Index("idx_fiscal_receipt_code", "receipt_code"),
    )

    id = Column(String, primary_key=True)

    order_id = Column(String, nullable=False, unique=True)

    receipt_code = Column(String(64), nullable=False, unique=True)
    document_type = Column(String(50), nullable=False)

    channel = Column(String(20))
    region = Column(String(10))

    amount_cents = Column(Integer, nullable=False)
    currency = Column(String(10), nullable=False)

    delivery_mode = Column(String(20))
    send_status = Column(String(50))
    send_target = Column(String(255))

    print_status = Column(String(50))
    print_site_path = Column(String(255))

    payload_json = Column(JSON, nullable=False)

    issued_at = Column(DateTime, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    