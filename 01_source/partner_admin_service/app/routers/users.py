from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.security import UserCreateIn, UserUpdateIn
from app.schemas.user_role import UserListOut, UserOut
from app.services import user_crud_service, user_role_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=UserListOut)
def list_users(db: Session = Depends(get_db)) -> UserListOut:
    return user_role_service.list_users(db)


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(body: UserCreateIn, db: Session = Depends(get_db)) -> UserOut:
    return user_crud_service.create_user(db, body)


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: str, db: Session = Depends(get_db)) -> UserOut:
    from app.schemas.user_role import UserOut as UO

    return UO.model_validate(user_role_service.get_user_or_404(db, user_id))


@router.patch("/{user_id}", response_model=UserOut)
def update_user(user_id: str, body: UserUpdateIn, db: Session = Depends(get_db)) -> UserOut:
    return user_crud_service.update_user(db, user_id, body)


@router.post("/{user_id}/deactivate", response_model=UserOut)
def deactivate_user(user_id: str, db: Session = Depends(get_db)) -> UserOut:
    return user_crud_service.deactivate_user(db, user_id)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: str, db: Session = Depends(get_db)) -> None:
    user_crud_service.delete_user(db, user_id)
