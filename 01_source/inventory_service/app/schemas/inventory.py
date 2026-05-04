from pydantic import BaseModel, Field


class MovementCreate(BaseModel):
    sku_id: str
    delta: int
    reason: str = Field(default="adjustment")


class InventoryOut(BaseModel):
    sku_id: str
    partner_id: str | None
    quantity_on_hand: int
    version: int

    model_config = {"from_attributes": True}


class LockerCreate(BaseModel):
    site_id: str
    name: str
    capacity_units: int = 0


class LockerOut(BaseModel):
    id: str
    site_id: str
    name: str
    capacity_units: int

    model_config = {"from_attributes": True}
