from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.api_key import ApiKeyListOut, ApiKeyRotateOut
from app.services import api_key_service

router = APIRouter(prefix="/lockers", tags=["api-keys"])


@router.post("/{locker_id}/api-keys/rotate", response_model=ApiKeyRotateOut)
def rotate_api_key(locker_id: str, db: Session = Depends(get_db)) -> ApiKeyRotateOut:
    return api_key_service.rotate_api_key(db, locker_id)


@router.get("/{locker_id}/api-keys", response_model=ApiKeyListOut)
def list_api_keys(locker_id: str, db: Session = Depends(get_db)) -> ApiKeyListOut:
    return api_key_service.list_api_keys(db, locker_id)
