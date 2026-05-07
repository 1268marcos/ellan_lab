from fastapi import APIRouter

from .deps import require_coo_access
from .portal import router as portal_router
from .portal_5180 import router as portal_5180_router

router = APIRouter()
router.include_router(portal_router)
router.include_router(portal_5180_router)

__all__ = ["router", "require_coo_access"]
