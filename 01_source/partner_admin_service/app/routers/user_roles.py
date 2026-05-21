from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.user_role import UserRoleCreateIn, UserRoleListOut, UserRoleOut, UserRoleUpdateIn
from app.services import user_role_service

router = APIRouter(prefix="/user-roles", tags=["user-roles"])


@router.get("", response_model=UserRoleListOut)
def list_roles(
    user_id: Optional[str] = Query(None),
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
) -> UserRoleListOut:
    roles = user_role_service.list_user_roles(db, user_id=user_id, active_only=active_only)
    return UserRoleListOut(roles=roles, total=len(roles))


@router.post("", response_model=UserRoleOut, status_code=status.HTTP_201_CREATED)
def create_role(body: UserRoleCreateIn, db: Session = Depends(get_db)) -> UserRoleOut:
    return user_role_service.create_user_role(db, body)


@router.get("/{role_id}", response_model=UserRoleOut)
def get_role(role_id: str, db: Session = Depends(get_db)) -> UserRoleOut:
    return UserRoleOut.model_validate(user_role_service.get_role_or_404(db, role_id))


@router.patch("/{role_id}", response_model=UserRoleOut)
def update_role(role_id: str, body: UserRoleUpdateIn, db: Session = Depends(get_db)) -> UserRoleOut:
    return user_role_service.update_user_role(db, role_id, body)


@router.post("/{role_id}/revoke", response_model=UserRoleOut)
def revoke_role(role_id: str, db: Session = Depends(get_db)) -> UserRoleOut:
    return user_role_service.revoke_user_role(db, role_id)


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(role_id: str, db: Session = Depends(get_db)) -> None:
    user_role_service.delete_user_role(db, role_id)
