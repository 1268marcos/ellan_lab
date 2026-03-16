# 01_source/order_pickup_service/app/schemas/dev_admin.py
from typing import Any

from pydantic import BaseModel, Field


class DevResetLockerIn(BaseModel):
    region: str = Field(..., description="SP ou PT")
    locker_id: str = Field(..., description="Locker físico a ser resetado")
    purge_local_data: bool = Field(
        default=True,
        description="Apaga Orders / Allocations / Pickups locais do locker",
    )
    release_known_allocations_first: bool = Field(
        default=True,
        description="Tenta soltar allocations locais antes de resetar os slots",
    )


class DevResetLockerOut(BaseModel):
    ok: bool
    region: str
    locker_id: str
    slots_total: int
    released_allocations: list[str]
    slot_reset_results: list[dict[str, Any]]
    deleted_pickups: int
    deleted_allocations: int
    deleted_orders: int
    message: str