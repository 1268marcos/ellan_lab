from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.cross_domain import PaymentPlayerRelation

router = APIRouter(prefix="/player-relations", tags=["player-relations"])


class PlayerRelationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    from_player_code: str
    to_player_code: str
    relation_type: str
    notes: str | None
    is_active: bool


class PlayerRelationListOut(BaseModel):
    items: list[PlayerRelationOut]
    total: int


@router.get("", response_model=PlayerRelationListOut)
def list_relations(
    from_player: str | None = Query(None),
    to_player: str | None = Query(None),
    relation_type: str | None = Query(None),
    limit: int = Query(200, le=500),
    db: Session = Depends(get_db),
) -> PlayerRelationListOut:
    q = db.query(PaymentPlayerRelation).filter(PaymentPlayerRelation.is_active.is_(True))
    if from_player:
        q = q.filter(PaymentPlayerRelation.from_player_code == from_player.upper())
    if to_player:
        q = q.filter(PaymentPlayerRelation.to_player_code == to_player.upper())
    if relation_type:
        q = q.filter(PaymentPlayerRelation.relation_type == relation_type.upper())
    items = q.order_by(PaymentPlayerRelation.relation_type).limit(limit).all()
    out = [PlayerRelationOut.model_validate(i) for i in items]
    return PlayerRelationListOut(items=out, total=len(out))
