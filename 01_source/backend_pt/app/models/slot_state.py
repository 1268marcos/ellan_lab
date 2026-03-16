# 01_source/backend_pt/app/models/slot_state.py
from pydantic import BaseModel
from typing import Literal

SlotState = Literal["AVAILABLE", "RESERVED", "PAID_PENDING_PICKUP", "OUT_OF_STOCK"]

class SetSlotStateIn(BaseModel):
    state: SlotState