from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.value_features import (
    RoutingRuleIn,
    RoutingRuleListOut,
    RoutingRuleOut,
    RoutingRuleUpdate,
)
from app.services import value_features_service

router = APIRouter(prefix="/routing-rules", tags=["routing-rules"])


@router.get("", response_model=RoutingRuleListOut)
def list_items(
    country_code: str | None = Query(None),
    payment_method: str | None = Query(None),
    active_only: bool = Query(True),
    limit: int = Query(100, le=300),
    db: Session = Depends(get_db),
) -> RoutingRuleListOut:
    items = value_features_service.list_routing_rules(
        db,
        country_code=country_code,
        payment_method=payment_method,
        active_only=active_only,
        limit=limit,
    )
    out = [RoutingRuleOut.model_validate(i) for i in items]
    return RoutingRuleListOut(items=out, total=len(out))


@router.get("/{rule_id}", response_model=RoutingRuleOut)
def get_item(rule_id: str, db: Session = Depends(get_db)) -> RoutingRuleOut:
    row = value_features_service.get_routing_rule(db, rule_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="routing_rule_not_found")
    return RoutingRuleOut.model_validate(row)


@router.post("", response_model=RoutingRuleOut, status_code=status.HTTP_201_CREATED)
def create_item(body: RoutingRuleIn, db: Session = Depends(get_db)) -> RoutingRuleOut:
    return RoutingRuleOut.model_validate(value_features_service.create_routing_rule(db, body))


@router.patch("/{rule_id}", response_model=RoutingRuleOut)
def update_item(
    rule_id: str, body: RoutingRuleUpdate, db: Session = Depends(get_db)
) -> RoutingRuleOut:
    row = value_features_service.update_routing_rule(db, rule_id, body)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="routing_rule_not_found")
    return RoutingRuleOut.model_validate(row)


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(rule_id: str, db: Session = Depends(get_db)) -> None:
    if not value_features_service.delete_routing_rule(db, rule_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="routing_rule_not_found")
