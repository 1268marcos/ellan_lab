from pydantic import BaseModel


class ReservationCreate(BaseModel):
    order_id: str
    sku_id: str
    quantity: int


class ReservationOut(BaseModel):
    id: str
    order_id: str
    sku_id: str
    quantity: int
    state: str
    version: int

    model_config = {"from_attributes": True}


class ReconciliationReport(BaseModel):
    sku_id: str
    expected_from_movements: int
    quantity_on_hand: int
    divergent: bool
