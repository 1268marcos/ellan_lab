from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.reservation import ReconciliationReport
from app.services import reconciliation_service
from metrics.inventory_metrics import set_divergences

router = APIRouter(prefix="/api/v1", tags=["reconciliation"])


@router.post("/reconciliation/run", response_model=list[ReconciliationReport])
def run_reconciliation(db: Session = Depends(get_db)) -> list[ReconciliationReport]:
    raw = reconciliation_service.reconcile_all(db)
    set_divergences(sum(1 for row in raw if row["divergent"]))
    return [ReconciliationReport(**row) for row in raw]
