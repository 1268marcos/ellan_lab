from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(String(64), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    products = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "products"

    sku_id = Column(String(36), primary_key=True)
    partner_id = Column(String(36), nullable=False, index=True)
    partner_sku = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category_id = Column(String(64), ForeignKey("categories.id"), nullable=False, index=True)
    amount_cents = Column(Integer, nullable=False)
    currency = Column(String(8), nullable=False, default="BRL")
    images_json = Column(Text, nullable=False, default="[]")
    is_active = Column(Boolean, nullable=False, default=True)
    is_deprecated = Column(Boolean, nullable=False, default=False)
    requires_signature = Column(Boolean, nullable=False, default=False)
    is_fragile = Column(Boolean, nullable=False, default=False)
    is_hazardous = Column(Boolean, nullable=False, default=False)
    temperature_zone = Column(String(32), nullable=False, default="AMBIENT")
    created_at = Column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (UniqueConstraint("partner_id", "partner_sku", name="uq_product_partner_sku"),)

    category = relationship("Category", back_populates="products")
    dimensions = relationship(
        "ProductDimensions",
        back_populates="product",
        uselist=False,
        cascade="all, delete-orphan",
    )
    compatibilities = relationship(
        "ProductCompatibility", back_populates="product", cascade="all, delete-orphan"
    )


class ProductDimensions(Base):
    __tablename__ = "product_dimensions"

    id = Column(String(36), primary_key=True)
    product_id = Column(String(36), ForeignKey("products.sku_id", ondelete="CASCADE"), nullable=False, unique=True)
    width_mm = Column(Integer, nullable=False)
    height_mm = Column(Integer, nullable=False)
    depth_mm = Column(Integer, nullable=False)
    weight_g = Column(Integer, nullable=False)

    product = relationship("Product", back_populates="dimensions")


class ProductCompatibility(Base):
    __tablename__ = "product_compatibilities"

    id = Column(String(36), primary_key=True)
    product_id = Column(String(36), ForeignKey("products.sku_id", ondelete="CASCADE"), nullable=False, index=True)
    locker_id = Column(String(36), nullable=False, index=True)
    locker_label = Column(String(255), nullable=True)
    recommended_slot_size = Column(String(32), nullable=True)
    slot_width_mm = Column(Integer, nullable=True)
    slot_height_mm = Column(Integer, nullable=True)
    slot_depth_mm = Column(Integer, nullable=True)
    max_weight_g = Column(Integer, nullable=True)
    temperature_zone = Column(String(32), nullable=True)
    signature_available = Column(Boolean, nullable=False, default=True)
    hazardous_allowed = Column(Boolean, nullable=False, default=False)

    product = relationship("Product", back_populates="compatibilities")


class PartnerProductRule(Base):
    __tablename__ = "partner_product_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    partner_id = Column(String(36), nullable=False, index=True)
    category_id = Column(String(64), ForeignKey("categories.id"), nullable=True, index=True)
    allowed_temperature_zones_json = Column(Text, nullable=False, default='["AMBIENT"]')
    max_weight_g = Column(Integer, nullable=True)
    requires_signature = Column(Boolean, nullable=True)
    is_hazardous_allowed = Column(Boolean, nullable=True)
    overrides_global = Column(Boolean, nullable=False, default=False)
