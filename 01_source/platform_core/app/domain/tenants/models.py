from dataclasses import dataclass


@dataclass
class Tenant:
    tenant_id: str
    legal_name: str
    slug: str
    status: str = "ACTIVE"
