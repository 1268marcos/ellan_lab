"""Portal COO (Chief Operations Officer): rotas base."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.schemas.coo import CooPortalMetaOut
from app.services.coo.portal import build_portal_meta

from .deps import require_coo_access

router = APIRouter(
    prefix="/api/v1/coo",
    tags=["COO Portal"],
)


@router.get("/meta", dependencies=[Depends(require_coo_access)])
async def get_portal_meta() -> CooPortalMetaOut:
    """Metadados do portal (base para layout e contrato com o frontend)."""
    return build_portal_meta()
