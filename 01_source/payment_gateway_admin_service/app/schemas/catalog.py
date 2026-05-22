from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PaymentMethodCatalogIn(BaseModel):
    code: str
    name: str
    family: str | None = None
    is_wallet: bool = False
    is_card: bool = False
    is_bnpl: bool = False
    is_cash_like: bool = False
    is_bank_transfer: bool = False
    is_instant: bool = False
    metadata_json: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


class PaymentMethodCatalogUpdate(BaseModel):
    name: str | None = None
    family: str | None = None
    is_wallet: bool | None = None
    is_card: bool | None = None
    is_bnpl: bool | None = None
    is_cash_like: bool | None = None
    is_bank_transfer: bool | None = None
    is_instant: bool | None = None
    metadata_json: dict[str, Any] | None = None
    is_active: bool | None = None


class PaymentMethodCatalogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    family: str | None
    is_wallet: bool
    is_card: bool
    is_bnpl: bool
    is_cash_like: bool
    is_bank_transfer: bool
    is_instant: bool
    metadata_json: dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class PaymentMethodCatalogListOut(BaseModel):
    items: list[PaymentMethodCatalogOut]
    total: int


class PaymentInterfaceCatalogIn(BaseModel):
    code: str
    name: str
    interface_type: str | None = None
    requires_hw: bool = False
    metadata_json: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


class PaymentInterfaceCatalogUpdate(BaseModel):
    name: str | None = None
    interface_type: str | None = None
    requires_hw: bool | None = None
    metadata_json: dict[str, Any] | None = None
    is_active: bool | None = None


class PaymentInterfaceCatalogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    interface_type: str | None
    requires_hw: bool
    metadata_json: dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class PaymentInterfaceCatalogListOut(BaseModel):
    items: list[PaymentInterfaceCatalogOut]
    total: int


class PaymentMethodUiAliasIn(BaseModel):
    id: str | None = None
    ui_code: str
    canonical_method_code: str
    default_payment_interface_code: str | None = None
    default_wallet_provider_code: str | None = None
    requires_customer_phone: bool = False
    requires_wallet_provider: bool = False
    is_active: bool = True


class PaymentMethodUiAliasUpdate(BaseModel):
    ui_code: str | None = None
    canonical_method_code: str | None = None
    default_payment_interface_code: str | None = None
    default_wallet_provider_code: str | None = None
    requires_customer_phone: bool | None = None
    requires_wallet_provider: bool | None = None
    is_active: bool | None = None


class PaymentMethodUiAliasOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    ui_code: str
    canonical_method_code: str
    default_payment_interface_code: str | None
    default_wallet_provider_code: str | None
    requires_customer_phone: bool
    requires_wallet_provider: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


class PaymentMethodUiAliasListOut(BaseModel):
    items: list[PaymentMethodUiAliasOut]
    total: int


class LockerPaymentMethodIn(BaseModel):
    locker_id: str
    method: str
    is_active: bool = True


class LockerPaymentMethodUpdate(BaseModel):
    is_active: bool | None = None


class LockerPaymentMethodOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    locker_id: str
    method: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class LockerPaymentMethodListOut(BaseModel):
    items: list[LockerPaymentMethodOut]
    total: int
