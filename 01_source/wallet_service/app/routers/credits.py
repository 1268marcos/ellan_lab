from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.wallet import ApplyCreditBody, ExpiredPickupBody
from app.services import credit_service

router = APIRouter(prefix="/api/v1", tags=["credits"])


class CreateCreditBody(BaseModel):
    user_id: str
    amount: int = Field(gt=0)
    promotional: bool = False
    expires_at: datetime | None = None


@router.post("/apply-credit", status_code=status.HTTP_201_CREATED)
def post_apply_credit(body: ApplyCreditBody, request: Request, db: Session = Depends(get_db)) -> dict:
    r = getattr(request.app.state, "redis", None)
    try:
        c, w, t = credit_service.apply_credit(db, r, body.user_id, body.credit_id, body.transaction_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"credit_id": c.id, "balance": w.balance, "transaction_id": t.transaction_id}


@router.post("/expired-pickup", status_code=status.HTTP_201_CREATED)
def post_expired_pickup(body: ExpiredPickupBody, request: Request, db: Session = Depends(get_db)) -> dict:
    r = getattr(request.app.state, "redis", None)
    try:
        w, t = credit_service.expire_pickup_debit(db, r, body.user_id, body.amount, body.transaction_id)
    except ValueError as e:
        if str(e) == "insufficient_funds":
            raise HTTPException(status_code=402, detail="insufficient_funds") from e
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"user_id": w.user_id, "balance": w.balance, "transaction_id": t.transaction_id}


@router.post("/credit-offer", status_code=status.HTTP_201_CREATED)
def post_credit_offer(body: CreateCreditBody, request: Request, db: Session = Depends(get_db)) -> dict:
    r = getattr(request.app.state, "redis", None)
    c = credit_service.create_promotional_credit(db, r, body.user_id, body.amount, body.promotional, body.expires_at)
    return {"credit_id": c.id, "remaining": c.remaining}
