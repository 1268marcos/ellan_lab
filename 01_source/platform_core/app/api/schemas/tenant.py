from pydantic import BaseModel, Field


class TenantCreateRequest(BaseModel):
    tenant_id: str = Field(..., min_length=1)
    legal_name: str = Field(..., min_length=1)
    slug: str = Field(..., min_length=1)
