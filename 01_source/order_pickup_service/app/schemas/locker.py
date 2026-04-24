# novo (API schemas)
# 01_source/order_pickup_service/app/schemas/locker.py

from __future__ import annotations

"""
Schemas Pydantic para API de Lockers.
"""


from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator


# ==================== SLOT CONFIG ====================
class SlotDimensions(BaseModel):
    """Dimensões no padrão de persistência: milímetros e gramas (inteiros)."""
    width_mm: Optional[int] = None
    height_mm: Optional[int] = None
    depth_mm: Optional[int] = None
    max_weight_g: Optional[int] = None


class LockerSlotConfigSchema(BaseModel):
    slot_size: str = Field(..., description="Tamanho: P, M, G, XG")
    slot_count: int = Field(..., ge=0)
    available_count: Optional[int] = None
    dimensions: Optional[SlotDimensions] = None


# ==================== PRODUCT CONFIG ====================
class ProductRequirements(BaseModel):
    requires_signature: bool = False
    requires_id: bool = False
    is_fragile: bool = False
    is_hazardous: bool = False


class ProductLockerConfigSchema(BaseModel):
    category: str
    subcategory: Optional[str] = None
    allowed: bool = True
    temperature_zone: str = "ANY"
    value_range: Optional[Dict[str, Optional[float]]] = None
    max_weight_kg: Optional[float] = None
    max_dimensions: Optional[Dict[str, Optional[int]]] = None
    requirements: Optional[ProductRequirements] = None
    priority: int = 100
    notes: Optional[str] = None


# ==================== ADDRESS ====================
class LockerAddressSchema(BaseModel):
    line: Optional[str] = None
    number: Optional[str] = None
    extra: Optional[str] = None
    district: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = "BR"
    latitude: Optional[float] = None
    longitude: Optional[float] = None


# ==================== LOCKER SCHEMAS ====================
class LockerCreateSchema(BaseModel):
    id: str = Field(..., min_length=5, max_length=64)
    external_id: Optional[str] = None
    display_name: str = Field(..., min_length=3, max_length=128)
    description: Optional[str] = None
    region: str = Field(..., min_length=2, max_length=8)
    site_id: Optional[str] = None
    timezone: str = "America/Sao_Paulo"
    address: Optional[LockerAddressSchema] = None
    active: bool = True
    slots_count: int = Field(default=24, ge=1)
    temperature_zone: str = "AMBIENT"
    security_level: str = "STANDARD"
    has_camera: bool = False
    has_alarm: bool = False
    access_hours: Optional[str] = None
    operator_id: Optional[str] = None
    tenant_id: Optional[str] = None
    is_rented: bool = False
    allowed_channels: str = "ONLINE,KIOSK,APP"
    allowed_payment_methods: str = "PIX,CARD,CASH"
    slot_configs: Optional[List[LockerSlotConfigSchema]] = None
    product_configs: Optional[List[ProductLockerConfigSchema]] = None


class LockerUpdateSchema(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    active: Optional[bool] = None
    temperature_zone: Optional[str] = None
    security_level: Optional[str] = None
    has_camera: Optional[bool] = None
    has_alarm: Optional[bool] = None
    access_hours: Optional[str] = None
    allowed_channels: Optional[str] = None
    allowed_payment_methods: Optional[str] = None
    metadata_json: Optional[str] = None


class LockerResponseSchema(BaseModel):
    id: str
    external_id: Optional[str]
    display_name: str
    description: Optional[str]
    region: str
    site_id: Optional[str]
    timezone: str
    address: Optional[Dict[str, Any]]
    active: bool
    slots_count: int
    allowed_channels: List[str]
    allowed_payment_methods: List[str]
    temperature_zone: str
    security_level: str
    has_camera: bool
    has_alarm: bool
    access_hours: Optional[str]
    operator_id: Optional[str]
    tenant_id: Optional[str]
    is_rented: bool
    slot_configs: List[Dict[str, Any]]
    allowed_product_categories: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LockerListResponseSchema(BaseModel):
    lockers: List[LockerResponseSchema]
    total: int
    region: Optional[str] = None


# ==================== OPERATOR SCHEMAS ====================
class LockerOperatorCreateSchema(BaseModel):
    id: str = Field(..., min_length=5, max_length=64)
    name: str = Field(..., min_length=3, max_length=128)
    document: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    operator_type: str = "LOGISTICS"
    commission_rate: Optional[float] = None
    currency: str = "BRL"


class LockerOperatorResponseSchema(BaseModel):
    id: str
    name: str
    document: Optional[str]
    operator_type: str
    active: bool
    commission_rate: Optional[float]
    currency: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== PRODUCT CATEGORY SCHEMAS ====================
class ProductCategoryCreateSchema(BaseModel):
    id: str = Field(..., min_length=3, max_length=64)
    name: str = Field(..., min_length=3, max_length=128)
    description: Optional[str] = None
    parent_category: Optional[str] = None
    default_temperature_zone: str = "AMBIENT"
    default_security_level: str = "STANDARD"
    is_hazardous: bool = False
    requires_age_verification: bool = False


class ProductCategoryResponseSchema(BaseModel):
    id: str
    name: str
    description: Optional[str]
    parent_category: Optional[str]
    default_temperature_zone: str
    default_security_level: str
    is_hazardous: bool
    requires_age_verification: bool

    class Config:
        from_attributes = True