from fastapi import APIRouter

from app.api.schemas.locker import LockerCreateRequest
from app.domain.lockers.models import Locker

router = APIRouter(prefix="/lockers", tags=["lockers"])


@router.post("")
def create_locker(payload: LockerCreateRequest) -> dict:
    locker = Locker(
        locker_id=payload.locker_id,
        tenant_id=payload.tenant_id,
        network_id=payload.network_id,
        site_id=payload.site_id,
        code=payload.code,
    )
    return {
        "locker_id": locker.locker_id,
        "tenant_id": locker.tenant_id,
        "network_id": locker.network_id,
        "site_id": locker.site_id,
        "code": locker.code,
        "status": locker.status,
    }
