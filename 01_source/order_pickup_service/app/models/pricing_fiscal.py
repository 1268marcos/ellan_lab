from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class ProductBundle(Base):
    __tablename__ = "product_bundles"

    __table_args__ = (
        Index("idx_pb_active_window", "is_active", "valid_from", "valid_until"),
        CheckConstraint("amount_cents >= 0", name="ck_pb_amount_non_negative"),
        CheckConstraint("valid_until IS NULL OR valid_until >= valid_from", name="ck_pb_valid_window"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="BRL")
    bundle_type: Mapped[str] = mapped_column(String(20), nullable=False, default="FIXED")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    valid_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )


class ProductBundleItem(Base):
    __tablename__ = "product_bundle_items"

    __table_args__ = (
        Index("idx_pbi_bundle_sort", "bundle_id", "sort_order"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bundle_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("product_bundles.id", ondelete="CASCADE"),
        nullable=False,
    )
    product_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("products.id"),
        nullable=False,
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    unit_price_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class Promotion(Base):
    __tablename__ = "promotions"

    __table_args__ = (
        Index("idx_promotions_active_window", "is_active", "valid_from", "valid_until"),
        CheckConstraint(
            "type IN ('PERCENT_OFF','FIXED_OFF','BUY_X_GET_Y','FREE_ITEM','BUNDLE_DISCOUNT')",
            name="ck_promotions_type",
        ),
        CheckConstraint("min_order_cents >= 0", name="ck_promotions_min_order_non_negative"),
        CheckConstraint("uses_count >= 0", name="ck_promotions_uses_count_non_negative"),
        CheckConstraint("max_uses IS NULL OR max_uses >= 0", name="ck_promotions_max_uses_non_negative"),
        CheckConstraint("max_discount_cents IS NULL OR max_discount_cents >= 0", name="ck_promotions_max_discount_non_negative"),
        CheckConstraint("valid_until IS NULL OR valid_until >= valid_from", name="ck_promotions_valid_window"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    code: Mapped[str | None] = mapped_column(String(32), nullable=True, unique=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    type: Mapped[str] = mapped_column(String(30), nullable=False)
    discount_pct: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    discount_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    min_order_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_discount_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_uses: Mapped[int | None] = mapped_column(Integer, nullable=True)
    uses_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    per_user_limit: Mapped[int | None] = mapped_column(Integer, nullable=True, default=1)
    conditions_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    campaign_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("promotion_campaigns.id", ondelete="SET NULL"), nullable=True
    )
    created_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )


class PromotionProductExclusion(Base):
    __tablename__ = "promotion_product_exclusions"

    promotion_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("promotions.id", ondelete="CASCADE"),
        primary_key=True,
    )
    product_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("products.id"),
        primary_key=True,
    )


class PromotionCampaign(Base):
    __tablename__ = "promotion_campaigns"

    __table_args__ = (
        Index("idx_promo_campaigns_active", "is_active", "valid_from", "valid_until"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    channel_family: Mapped[str] = mapped_column(String(32), nullable=False, default="GENERAL")
    primary_country: Mapped[str | None] = mapped_column(String(8), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    max_stack_promotions: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )


class PromotionScope(Base):
    __tablename__ = "promotion_scopes"

    __table_args__ = (
        Index("idx_promotion_scopes_promo", "promotion_id", "scope_type"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    promotion_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("promotions.id", ondelete="CASCADE"), nullable=False
    )
    scope_type: Mapped[str] = mapped_column(String(32), nullable=False)
    scope_value: Mapped[str] = mapped_column(String(128), nullable=False)
    mode: Mapped[str] = mapped_column(String(16), nullable=False, default="INCLUDE")
    notes: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )


class PromotionProductInclusion(Base):
    __tablename__ = "promotion_product_inclusions"

    promotion_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("promotions.id", ondelete="CASCADE"),
        primary_key=True,
    )
    product_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("products.id"),
        primary_key=True,
    )


class PromotionRedemption(Base):
    __tablename__ = "promotion_redemptions"

    __table_args__ = (
        Index("idx_promo_redemptions_promo_at", "promotion_id", "redeemed_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    promotion_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("promotions.id", ondelete="RESTRICT"), nullable=False
    )
    campaign_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("promotion_campaigns.id", ondelete="SET NULL"), nullable=True
    )
    order_id: Mapped[str] = mapped_column(String(64), nullable=False)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    partner_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    channel_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    country_code: Mapped[str | None] = mapped_column(String(8), nullable=True)
    player_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    discount_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="BRL")
    idempotency_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    redeemed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)


class FiscalAutoClassificationLog(Base):
    __tablename__ = "fiscal_auto_classification_log"

    __table_args__ = (
        Index("idx_facl_order", "order_id"),
        Index("idx_facl_source_classified", "source", "classified_at"),
        CheckConstraint(
            "source IN ('AUTO_PRODUCT_CONFIG','CATEGORY_FALLBACK','MANUAL','DEFAULT')",
            name="ck_facl_source",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[str] = mapped_column(String(36), nullable=False)
    invoice_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sku_id: Mapped[str] = mapped_column(String(255), nullable=False)
    ncm_applied: Mapped[str | None] = mapped_column(String(10), nullable=True)
    icms_cst_applied: Mapped[str | None] = mapped_column(String(3), nullable=True)
    pis_cst_applied: Mapped[str | None] = mapped_column(String(2), nullable=True)
    cofins_cst_applied: Mapped[str | None] = mapped_column(String(2), nullable=True)
    cfop_applied: Mapped[str | None] = mapped_column(String(5), nullable=True)
    source: Mapped[str] = mapped_column(String(20), nullable=False)
    classified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
