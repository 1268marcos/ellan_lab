from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint

from app.core.db import Base


class ProductMedia(Base):
    __tablename__ = "product_media"

    __table_args__ = (
        CheckConstraint("media_type IN ('IMAGE','VIDEO','PDF','3D')", name="ck_pm_media_type"),
        Index("idx_pm_product_sort", "product_id", "sort_order"),
        Index("idx_pm_primary", "product_id", "is_primary"),
    )

    id = Column(String(36), primary_key=True)
    product_id = Column(String(255), ForeignKey("products.id"), nullable=False, index=True)
    media_type = Column(String(10), nullable=False)
    url = Column(String(500), nullable=False)
    cdn_key = Column(String(255), nullable=True)
    alt_text = Column(String(255), nullable=True)
    sort_order = Column(Integer, nullable=False, default=0)
    is_primary = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class ProductBarcode(Base):
    __tablename__ = "product_barcodes"

    __table_args__ = (
        CheckConstraint(
            "barcode_type IN ('EAN13','EAN8','GTIN14','QR','CODE128','DATAMATRIX')",
            name="ck_pb_barcode_type",
        ),
        UniqueConstraint("barcode_value", name="ux_product_barcodes_value"),
        Index("idx_pb_product_type", "product_id", "barcode_type"),
        Index("idx_pb_primary", "product_id", "is_primary"),
    )

    id = Column(String(36), primary_key=True)
    product_id = Column(String(255), ForeignKey("products.id"), nullable=False, index=True)
    barcode_type = Column(String(20), nullable=False)
    barcode_value = Column(String(128), nullable=False)
    is_primary = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
