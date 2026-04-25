from __future__ import annotations

from pydantic import BaseModel, Field


class PartnerStatusTransitionIn(BaseModel):
    to_status: str = Field(..., description="Novo status do parceiro")
    reason: str | None = Field(default=None, description="Motivo da transição")


class PartnerStatusOut(BaseModel):
    ok: bool
    partner_id: str
    partner_type: str
    from_status: str | None = None
    to_status: str
    changed_by: str | None = None
    changed_at: str


class PartnerStatusHistoryItemOut(BaseModel):
    id: str
    partner_id: str
    partner_type: str
    from_status: str | None = None
    to_status: str
    reason: str | None = None
    changed_by: str | None = None
    changed_at: str


class PartnerStatusHistoryListOut(BaseModel):
    ok: bool
    total: int
    items: list[PartnerStatusHistoryItemOut]


class PartnerContactIn(BaseModel):
    contact_type: str = Field(..., description="COMMERCIAL|TECHNICAL|BILLING|EMERGENCY")
    name: str = Field(..., min_length=1, max_length=128)
    email: str | None = Field(default=None, max_length=128)
    phone: str | None = Field(default=None, max_length=32)
    is_primary: bool = Field(default=False)


class PartnerContactPatchIn(BaseModel):
    contact_type: str | None = Field(default=None, description="COMMERCIAL|TECHNICAL|BILLING|EMERGENCY")
    name: str | None = Field(default=None, min_length=1, max_length=128)
    email: str | None = Field(default=None, max_length=128)
    phone: str | None = Field(default=None, max_length=32)
    is_primary: bool | None = Field(default=None)


class PartnerContactOut(BaseModel):
    id: str
    partner_id: str
    partner_type: str
    contact_type: str
    name: str
    email: str | None = None
    phone: str | None = None
    is_primary: bool
    created_at: str
    updated_at: str


class PartnerContactListOut(BaseModel):
    ok: bool
    total: int
    items: list[PartnerContactOut]


class PartnerSlaAgreementIn(BaseModel):
    country: str = Field(default="BR", min_length=2, max_length=2)
    product_category: str | None = Field(default=None, max_length=64)
    sla_pickup_hours: int = Field(default=72, ge=1, le=720)
    sla_return_hours: int = Field(default=24, ge=1, le=720)
    penalty_pct: float = Field(default=0, ge=0, le=100)
    valid_from: str = Field(..., description="Data YYYY-MM-DD")
    valid_until: str | None = Field(default=None, description="Data YYYY-MM-DD")
    is_active: bool = Field(default=True)


class PartnerSlaAgreementPatchIn(BaseModel):
    country: str | None = Field(default=None, min_length=2, max_length=2)
    product_category: str | None = Field(default=None, max_length=64)
    sla_pickup_hours: int | None = Field(default=None, ge=1, le=720)
    sla_return_hours: int | None = Field(default=None, ge=1, le=720)
    penalty_pct: float | None = Field(default=None, ge=0, le=100)
    valid_from: str | None = Field(default=None, description="Data YYYY-MM-DD")
    valid_until: str | None = Field(default=None, description="Data YYYY-MM-DD")
    is_active: bool | None = Field(default=None)


class PartnerSlaAgreementOut(BaseModel):
    id: str
    partner_id: str
    partner_type: str
    country: str
    product_category: str | None = None
    sla_pickup_hours: int
    sla_return_hours: int
    penalty_pct: float
    valid_from: str
    valid_until: str | None = None
    is_active: bool
    created_at: str


class PartnerSlaAgreementListOut(BaseModel):
    ok: bool
    total: int
    items: list[PartnerSlaAgreementOut]


class PartnerDeleteOut(BaseModel):
    ok: bool
    id: str
    message: str
