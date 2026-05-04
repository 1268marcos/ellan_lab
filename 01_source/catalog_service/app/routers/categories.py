from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.category import Category
from app.schemas.category import CategoryOut

router = APIRouter(tags=["categories"])


@router.get("/categories", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)) -> list[Category]:
    return db.query(Category).filter(Category.is_active.is_(True)).order_by(Category.name).all()
