from fastapi import APIRouter

from app.api.schemas.tenant import TenantCreateRequest
from app.domain.tenants.models import Tenant

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.post("")
def create_tenant(payload: TenantCreateRequest) -> dict:
    tenant = Tenant(
        tenant_id=payload.tenant_id,
        legal_name=payload.legal_name,
        slug=payload.slug,
    )
    return {
        "tenant_id": tenant.tenant_id,
        "legal_name": tenant.legal_name,
        "slug": tenant.slug,
        "status": tenant.status,
    }
