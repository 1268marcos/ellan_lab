# Schemas para itens de pedido (order_items) — API interna + campos opcionais em criação de pedido.

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


def normalize_ncm_optional(value: str | None) -> str | None:
    """Extrai apenas dígitos; None se vazio; alinhado a VARCHAR(10) no banco."""
    if value is None:
        return None
    digits = "".join(c for c in str(value).strip() if c.isdigit())
    if not digits:
        return None
    if len(digits) > 10:
        raise ValueError("ncm: no máximo 10 dígitos")
    if len(digits) < 2:
        raise ValueError("ncm: informe ao menos 2 dígitos")
    return digits


class OrderItemCreateIn(BaseModel):
    """POST /internal/orders/{order_id}/items"""

    sku_id: str = Field(..., min_length=1, max_length=255)
    sku_description: str | None = Field(default=None, max_length=255)
    ncm: str | None = Field(default=None, max_length=32, description="NCM Mercosul (apenas dígitos armazenados)")
    quantity: int = Field(default=1, ge=1, le=999_999)
    unit_amount_cents: int = Field(..., ge=0)
    total_amount_cents: int | None = Field(default=None, ge=0)
    slot_preference: int | None = Field(default=None, ge=0)
    slot_size: str | None = Field(default=None, max_length=20)
    item_status: str | None = Field(default="PENDING", max_length=32)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("sku_id")
    @classmethod
    def strip_sku(cls, v: str) -> str:
        s = (v or "").strip()
        if not s:
            raise ValueError("sku_id é obrigatório")
        return s

    @field_validator("ncm", mode="before")
    @classmethod
    def validate_ncm(cls, v):
        if v is None:
            return None
        if isinstance(v, (int, float)):
            v = str(int(v))
        if isinstance(v, str) and not v.strip():
            return None
        return normalize_ncm_optional(str(v).strip())

    @model_validator(mode="after")
    def total_or_derive(self):
        if self.total_amount_cents is None:
            object.__setattr__(self, "total_amount_cents", int(self.quantity) * int(self.unit_amount_cents))
        return self


class OrderItemPatchIn(BaseModel):
    """PATCH /internal/orders/{order_id}/items/{item_id}"""

    sku_description: str | None = Field(default=None, max_length=255)
    ncm: str | None = Field(default=None, max_length=32)
    quantity: int | None = Field(default=None, ge=1, le=999_999)
    unit_amount_cents: int | None = Field(default=None, ge=0)
    total_amount_cents: int | None = Field(default=None, ge=0)
    slot_preference: int | None = Field(default=None, ge=0)
    slot_size: str | None = Field(default=None, max_length=20)
    item_status: str | None = Field(default=None, max_length=32)
    metadata: dict[str, Any] | None = None

    @field_validator("ncm", mode="before")
    @classmethod
    def validate_ncm(cls, v):
        if v is None:
            return None
        if isinstance(v, (int, float)):
            v = str(int(v))
        if isinstance(v, str) and not v.strip():
            return None
        return normalize_ncm_optional(str(v).strip())


class OrderItemOut(BaseModel):
    id: int
    order_id: str
    sku_id: str
    sku_description: str | None
    ncm: str | None
    quantity: int
    unit_amount_cents: int
    total_amount_cents: int
    slot_preference: int | None
    slot_size: str | None
    item_status: str
    metadata: dict[str, Any]

    @classmethod
    def from_orm_item(cls, row: Any) -> "OrderItemOut":
        return cls(
            id=row.id,
            order_id=row.order_id,
            sku_id=row.sku_id,
            sku_description=row.sku_description,
            ncm=row.ncm,
            quantity=row.quantity,
            unit_amount_cents=row.unit_amount_cents,
            total_amount_cents=row.total_amount_cents,
            slot_preference=row.slot_preference,
            slot_size=row.slot_size,
            item_status=row.item_status,
            metadata=dict(row.metadata_json or {}),
        )
