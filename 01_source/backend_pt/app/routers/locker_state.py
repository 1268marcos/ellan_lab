from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
from pydantic import BaseModel
from typing import Literal

router = APIRouter(prefix="/locker", tags=["locker"])

SlotState = Literal["AVAILABLE", "RESERVED", "PAID_PENDING_PICKUP", "OUT_OF_STOCK"]

class SetSlotStateIn(BaseModel):
    state: SlotState

# MVP: estado em memória (depois você troca por Redis/Postgres)
SLOT_STATE = {i: "AVAILABLE" for i in range(1, 25)}

@router.post("/slots/{slot}/set-state")
def set_slot_state(slot: int, payload: SetSlotStateIn):
    if slot < 1 or slot > 24:
        raise HTTPException(status_code=400, detail="slot must be 1..24")

    SLOT_STATE[slot] = payload.state
    now = datetime.now(timezone.utc)
    return {
        "ok": True,
        "slot": slot,
        "state": payload.state,
        "updated_at": now.isoformat(),
    }