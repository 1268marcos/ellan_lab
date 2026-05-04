from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.wallet import BalanceOut
from app.services import wallet_service
router = APIRouter(prefix="/api/v1", tags=["wallet"])


@router.get("/balance/{user_id}", response_model=BalanceOut)
def get_balance(user_id: str, request: Request, db: Session = Depends(get_db)) -> BalanceOut:
    r = getattr(request.app.state, "redis", None)
    cached = wallet_service.get_cached_balance(r, user_id)
    if cached is not None:
        w = wallet_service.get_or_create_wallet(db, user_id)
        return BalanceOut(user_id=user_id, balance=cached, version=w.version)
    w = wallet_service.get_or_create_wallet(db, user_id)
    wallet_service.set_cached_balance(r, user_id, w.balance)
    return BalanceOut(user_id=w.user_id, balance=w.balance, version=w.version)
