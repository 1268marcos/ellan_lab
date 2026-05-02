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


class ProductCategoryUpdateIn(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=4000)
    parent_category: str | None = Field(default=None, max_length=64)
    is_active: bool | None = None
    metadata_json: dict[str, Any] | None = None


class ProductCategoryDeleteOut(BaseModel):
    ok: bool
    id: str
