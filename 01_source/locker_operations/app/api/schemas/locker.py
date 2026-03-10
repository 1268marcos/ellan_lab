from pydantic import BaseModel, Field


class LockerCreateRequest(BaseModel):
    locker_id: str = Field(..., min_length=1)
    network_id: str = Field(..., min_length=1)
    site_id: str = Field(..., min_length=1)
    code: str = Field(..., min_length=1)
    tenant_id: str | None = None
