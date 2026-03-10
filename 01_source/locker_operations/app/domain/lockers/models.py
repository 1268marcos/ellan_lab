from dataclasses import dataclass


@dataclass
class Locker:
    locker_id: str
    tenant_id: str | None
    network_id: str
    site_id: str
    code: str
    status: str = "ACTIVE"
