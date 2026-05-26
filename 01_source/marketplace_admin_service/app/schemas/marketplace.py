from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class SellerCreateIn(BaseModel):
    legal_name: str
    trade_name: Optional[str] = None
    tax_id: str
    email: str
    phone: Optional[str] = None
    website: Optional[str] = None
    commission_pct: Decimal = Field(default=Decimal("5.00"))
    monthly_fee_cents: int = 0
    status: str = "PENDING_APPROVAL"


class SellerUpdateIn(BaseModel):
    legal_name: Optional[str] = None
    trade_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    status: Optional[str] = None
    commission_pct: Optional[Decimal] = None
    monthly_fee_cents: Optional[int] = None


class SellerOut(BaseModel):
    id: str
    legal_name: str
    trade_name: Optional[str] = None
    tax_id: str
    email: str
    phone: Optional[str] = None
    website: Optional[str] = None
    status: str
    commission_pct: Decimal
    monthly_fee_cents: int
    seller_rating: Optional[Decimal] = None
    total_sales_cents: int
    total_orders: int
    joined_at: datetime
    approved_at: Optional[datetime] = None
    suspended_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SellerListOut(BaseModel):
    sellers: list[SellerOut]
    total: int


class SellerProductCreateIn(BaseModel):
    seller_id: str
    locker_id: str
    product_id: str
    seller_sku: Optional[str] = None
    price_cents: int
    quantity: int = 0
    max_quantity_per_order: int = 10
    status: str = "ACTIVE"
    priority: int = 100


class SellerProductUpdateIn(BaseModel):
    price_cents: Optional[int] = None
    quantity: Optional[int] = None
    max_quantity_per_order: Optional[int] = None
    status: Optional[str] = None
    priority: Optional[int] = None
    seller_sku: Optional[str] = None


class SellerProductOut(BaseModel):
    id: str
    seller_id: str
    locker_id: str
    product_id: str
    seller_sku: Optional[str] = None
    price_cents: int
    quantity: int
    max_quantity_per_order: int
    status: str
    priority: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SellerProductListOut(BaseModel):
    products: list[SellerProductOut]
    total: int


class CommissionCreateIn(BaseModel):
    seller_id: str
    order_id: str
    order_item_id: Optional[int] = None
    commission_rate_pct: Decimal
    commission_amount_cents: int
    ellan_fee_cents: int
    payment_gateway_fee_cents: int
    net_to_seller_cents: int
    status: str = "PENDING"


class CommissionUpdateIn(BaseModel):
    status: Optional[str] = None
    settled_at: Optional[datetime] = None


class CommissionOut(BaseModel):
    id: str
    seller_id: str
    order_id: str
    order_item_id: Optional[int] = None
    commission_rate_pct: Decimal
    commission_amount_cents: int
    ellan_fee_cents: int
    payment_gateway_fee_cents: int
    net_to_seller_cents: int
    status: str
    settled_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CommissionListOut(BaseModel):
    commissions: list[CommissionOut]
    total: int


class CommissionNetPreviewOut(BaseModel):
    price_cents: int
    commission_pct: Decimal
    commission_cents: int
    ellan_fee_cents: int
    gateway_fee_cents: int
    net_cents: int


class SellerReviewCreateIn(BaseModel):
    seller_id: str
    order_id: str
    user_id: Optional[str] = None
    rating: int
    comment: Optional[str] = None
    delivery_rating: Optional[int] = None
    product_quality_rating: Optional[int] = None
    communication_rating: Optional[int] = None
    verified_purchase: bool = True


class SellerReviewOut(BaseModel):
    id: str
    seller_id: str
    order_id: str
    user_id: Optional[str] = None
    rating: int
    comment: Optional[str] = None
    delivery_rating: Optional[int] = None
    product_quality_rating: Optional[int] = None
    communication_rating: Optional[int] = None
    verified_purchase: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class SellerReviewListOut(BaseModel):
    reviews: list[SellerReviewOut]
    total: int
