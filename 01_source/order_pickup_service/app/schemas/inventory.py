from __future__ import annotations

from pydantic import BaseModel, Field


class ProductInventoryItemOut(BaseModel):
    id: str
    product_id: str
    locker_id: str
    slot_size: str
    quantity_on_hand: int
    quantity_reserved: int
    quantity_available: int
    reorder_point: int
    reorder_quantity: int
    last_counted_at: str | None = None
    updated_at: str


class ProductInventoryListOut(BaseModel):
    ok: bool
    total: int
    limit: int
    offset: int
    items: list[ProductInventoryItemOut]


class InventoryRestockIn(BaseModel):
    product_id: str = Field(..., max_length=255)
    slot_size: str = Field(..., max_length=8)
    quantity: int = Field(..., ge=1, le=100000)
    note: str | None = Field(default=None, max_length=1000)


class InventoryRestockOut(BaseModel):
    ok: bool
    inventory: ProductInventoryItemOut
    movement_id: str


class InventoryReserveIn(BaseModel):
    order_id: str = Field(..., max_length=64)
    product_id: str = Field(..., max_length=255)
    locker_id: str = Field(..., max_length=64)
    slot_size: str = Field(..., max_length=8)
    quantity: int = Field(default=1, ge=1, le=100000)
    expires_in_minutes: int = Field(default=30, ge=1, le=24 * 60)
    note: str | None = Field(default=None, max_length=1000)


class InventoryReservationOut(BaseModel):
    id: str
    order_id: str
    product_id: str
    locker_id: str
    slot_size: str
    quantity: int
    status: str
    expires_at: str
    updated_at: str


class InventoryReserveOut(BaseModel):
    ok: bool
    idempotent: bool
    reservation: InventoryReservationOut
    inventory: ProductInventoryItemOut
    movement_id: str


class InventoryReservationActionOut(BaseModel):
    ok: bool
    reservation: InventoryReservationOut
    inventory: ProductInventoryItemOut
    movement_id: str


class InventoryReservationReconciliationItemOut(BaseModel):
    product_id: str
    locker_id: str
    slot_size: str
    reserved_stored: int
    reserved_active: int
    delta: int
    status: str


class InventoryReservationReconciliationOut(BaseModel):
    ok: bool
    checked_at: str
    auto_fixed: int
    divergence_alerts: int
    orphan_active_groups: int
    items: list[InventoryReservationReconciliationItemOut]


class InventoryReservationHealthRankItemOut(BaseModel):
    product_id: str
    locker_id: str
    slot_size: str
    divergence_events_current: int
    divergence_events_previous: int
    divergence_events_delta_pct: float
    abs_delta_sum_current: int
    abs_delta_sum_previous: int
    abs_delta_sum_delta_pct: float
    auto_fixes_current: int
    auto_fixes_previous: int
    orphan_alerts_current: int
    orphan_alerts_previous: int
    trend: str


class InventoryReservationHealthOut(BaseModel):
    ok: bool
    period_from: str
    period_to: str
    previous_from: str
    previous_to: str
    divergence_events_current: int
    divergence_events_previous: int
    divergence_events_delta_pct: float
    auto_fixes_current: int
    auto_fixes_previous: int
    auto_fixes_delta_pct: float
    orphan_alerts_current: int
    orphan_alerts_previous: int
    orphan_alerts_delta_pct: float
    entities_with_divergence_current: int
    entities_with_divergence_previous: int
    ranking: list[InventoryReservationHealthRankItemOut]


class InventoryReservationExpiryRunOut(BaseModel):
    ok: bool
    changed: int
    message: str


class InventoryReservationListOut(BaseModel):
    ok: bool
    total: int
    limit: int
    offset: int
    period_from: str | None = None
    period_to: str | None = None
    status_filter: str | None = None
    items: list[InventoryReservationOut]


class InventoryLowStockItemOut(BaseModel):
    id: str
    product_id: str
    locker_id: str
    slot_size: str
    quantity_on_hand: int
    quantity_reserved: int
    quantity_available: int
    reorder_point: int
    reorder_quantity: int
    updated_at: str


class InventoryLowStockListOut(BaseModel):
    ok: bool
    total: int
    limit: int
    offset: int
    threshold: int
    items: list[InventoryLowStockItemOut]
