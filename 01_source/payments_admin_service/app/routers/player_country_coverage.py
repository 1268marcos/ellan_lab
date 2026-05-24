from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.cross_domain import PaymentPlayerCountryCoverage
from app.schemas.ecosystem_pro import PlayerCountryCoverageListOut, PlayerCountryCoverageOut

router = APIRouter(prefix="/player-country-coverage", tags=["player-country-coverage"])


@router.get("", response_model=PlayerCountryCoverageListOut)
def list_coverage(
    country_code: str | None = Query(None),
    player_code: str | None = Query(None),
    limit: int = Query(300, le=1000),
    db: Session = Depends(get_db),
) -> PlayerCountryCoverageListOut:
    q = db.query(PaymentPlayerCountryCoverage)
    if country_code:
        q = q.filter(PaymentPlayerCountryCoverage.country_code == country_code.upper())
    if player_code:
        q = q.filter(PaymentPlayerCountryCoverage.player_code == player_code.upper())
    items = q.order_by(
        PaymentPlayerCountryCoverage.country_code,
        PaymentPlayerCountryCoverage.player_code,
    ).limit(limit).all()
    out = [PlayerCountryCoverageOut.model_validate(i) for i in items]
    return PlayerCountryCoverageListOut(items=out, total=len(out))
