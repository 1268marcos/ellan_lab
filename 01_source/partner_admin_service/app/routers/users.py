from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.user_role import UserListOut
from app.services import user_role_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=UserListOut)
def list_users(db: Session = Depends(get_db)) -> UserListOut:
    return user_role_service.list_users(db)
