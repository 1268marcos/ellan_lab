from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.transaction import ReconcileReport
from app.schemas.wallet import CreditBody, DebitBody
from app.services import reconciliation_service, wallet_service

router = APIRouter(prefix="/api/v1", tags=["transactions"])


@router.post("/credit", status_code=status.HTTP_201_CREATED)
def post_credit(body: CreditBody, request: Request, db: Session = Depends(get_db)) -> dict:
    r = getattr(request.app.state, "redis", None)
    try:
        w, t = wallet_service.credit_wallet(db, r, body.user_id, body.amount, body.transaction_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"user_id": w.user_id, "balance": w.balance, "version": w.version, "transaction_id": t.transaction_id}


@router.post("/debit", status_code=status.HTTP_201_CREATED)
def post_debit(body: DebitBody, request: Request, db: Session = Depends(get_db)) -> dict:
    r = getattr(request.app.state, "redis", None)
    try:
        w, t = wallet_service.debit_wallet(
            db, r, body.user_id, body.amount, body.transaction_id, expected_version=body.version
        )
    except wallet_service.OptimisticLockError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    except ValueError as e:
        if str(e) == "insufficient_funds":
            raise HTTPException(status_code=402, detail="insufficient_funds") from e
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"user_id": w.user_id, "balance": w.balance, "version": w.version, "transaction_id": t.transaction_id}


@router.post("/reconcile", response_model=list[ReconcileReport])
def post_reconcile(db: Session = Depends(get_db)) -> list[ReconcileReport]:
    raw = reconciliation_service.reconcile_all(db)
    return [ReconcileReport(**row) for row in raw]
