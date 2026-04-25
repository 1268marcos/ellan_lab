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
