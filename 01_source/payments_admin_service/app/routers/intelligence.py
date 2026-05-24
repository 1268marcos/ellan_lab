from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.cross_domain import PaymentIntelligenceSummary, PaymentOrderGraphOut
from app.schemas.value_features import EcosystemGraphOut, GlobalReadinessOut, RoutingSuggestionOut
from app.services import intelligence_service, value_features_service

router = APIRouter(prefix="/intelligence", tags=["intelligence"])


@router.get("/summary", response_model=PaymentIntelligenceSummary)
def summary(db: Session = Depends(get_db)) -> PaymentIntelligenceSummary:
    return intelligence_service.build_summary(db)


@router.get("/order-graph/{order_id}", response_model=PaymentOrderGraphOut)
def order_graph(order_id: str, db: Session = Depends(get_db)) -> PaymentOrderGraphOut:
    return intelligence_service.build_order_graph(db, order_id)


@router.get("/ecosystem-graph", response_model=EcosystemGraphOut)
def ecosystem_graph(db: Session = Depends(get_db)) -> EcosystemGraphOut:
    return value_features_service.build_ecosystem_graph(db)


@router.get("/global-readiness", response_model=GlobalReadinessOut)
def global_readiness(db: Session = Depends(get_db)) -> GlobalReadinessOut:
    return value_features_service.build_global_readiness(db)


@router.get("/routing-suggest", response_model=RoutingSuggestionOut)
def routing_suggest(
    country_code: str = Query(..., min_length=2, max_length=2),
    payment_method: str = Query(...),
    amount_cents: int | None = Query(None, ge=0),
    sales_channel: str | None = Query(None),
    db: Session = Depends(get_db),
) -> RoutingSuggestionOut:
    result = value_features_service.suggest_routing(
        db,
        country_code=country_code,
        payment_method=payment_method,
        amount_cents=amount_cents,
        sales_channel=sales_channel,
    )
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="no_routing_rule")
    return result
