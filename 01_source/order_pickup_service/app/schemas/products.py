from __future__ import annotations

from pydantic import BaseModel, Field


class ProductStatusTransitionIn(BaseModel):
    to_status: str = Field(..., max_length=30)
    reason: str | None = Field(default=None, max_length=1000)


class ProductStatusOut(BaseModel):
    ok: bool
    product_id: str
    from_status: str
    to_status: str
    changed_by: str | None = None
    changed_at: str


class ProductStatusHistoryItemOut(BaseModel):
    id: str
    product_id: str
    from_status: str | None = None
    to_status: str
    reason: str | None = None
    changed_by: str | None = None
    changed_at: str


class ProductStatusHistoryListOut(BaseModel):
    ok: bool
    total: int
    items: list[ProductStatusHistoryItemOut]


class ProductListItemOut(BaseModel):
    id: str
    name: str
    category_id: str | None = None
    status: str
    is_active: bool
    updated_at: str


class ProductListOut(BaseModel):
    ok: bool
    total: int
    limit: int
    offset: int
    items: list[ProductListItemOut]


class ProductMediaCreateIn(BaseModel):
    media_type: str = Field(..., max_length=10, description="IMAGE|VIDEO|PDF|3D")
    url: str = Field(..., max_length=500)
    cdn_key: str | None = Field(default=None, max_length=255)
    alt_text: str | None = Field(default=None, max_length=255)
    sort_order: int = Field(default=0, ge=0, le=9999)
    is_primary: bool = Field(default=False)


class ProductMediaOut(BaseModel):
    id: str
    product_id: str
    media_type: str
    url: str
    cdn_key: str | None = None
    alt_text: str | None = None
    sort_order: int
    is_primary: bool
    created_at: str


class ProductMediaListOut(BaseModel):
    ok: bool
    total: int
    items: list[ProductMediaOut]


class ProductBarcodeCreateIn(BaseModel):
    barcode_type: str = Field(..., max_length=20, description="EAN13|EAN8|GTIN14|QR|CODE128|DATAMATRIX")
    barcode_value: str = Field(..., max_length=128)
    is_primary: bool = Field(default=False)


class ProductBarcodeOut(BaseModel):
    id: str
    product_id: str
    barcode_type: str
    barcode_value: str
    is_primary: bool
    created_at: str


class ProductBarcodeListOut(BaseModel):
    ok: bool
    total: int
    items: list[ProductBarcodeOut]
