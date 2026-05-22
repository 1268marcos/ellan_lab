from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ProductCategoryOut(BaseModel):
    id: str
    name: str
    description: str | None = None
    parent_category: str | None = None
    is_active: bool = True
    metadata_json: dict[str, Any] = Field(default_factory=dict)
    requires_age_verification: bool = False
    requires_id: bool = False
    requires_signature: bool = False
    max_weight_g: int | None = None
    max_width_mm: int | None = None
    max_height_mm: int | None = None
    max_depth_mm: int | None = None
    created_at: str
    updated_at: str


class ProductCategoryListOut(BaseModel):
    ok: bool
    items: list[ProductCategoryOut]


class ProductCategoryCreateIn(BaseModel):
    id: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=4000)
    parent_category: str | None = Field(default=None, max_length=64)
    is_active: bool = True
    metadata_json: dict[str, Any] | None = None
    requires_age_verification: bool = False
    requires_id: bool = False
    requires_signature: bool = False
    max_weight_g: int | None = Field(default=None, ge=0)
    max_width_mm: int | None = Field(default=None, ge=0)
    max_height_mm: int | None = Field(default=None, ge=0)
    max_depth_mm: int | None = Field(default=None, ge=0)


class ProductCategoryUpdateIn(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=4000)
    parent_category: str | None = Field(default=None, max_length=64)
    is_active: bool | None = None
    metadata_json: dict[str, Any] | None = None
    requires_age_verification: bool | None = None
    requires_id: bool | None = None
    requires_signature: bool | None = None
    max_weight_g: int | None = Field(default=None, ge=0)
    max_width_mm: int | None = Field(default=None, ge=0)
    max_height_mm: int | None = Field(default=None, ge=0)
    max_depth_mm: int | None = Field(default=None, ge=0)


class ProductCategoryDeleteOut(BaseModel):
    ok: bool
    id: str
