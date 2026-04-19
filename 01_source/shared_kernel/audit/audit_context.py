from dataclasses import dataclass
from datetime import datetime, timezone

from shared_kernel.observability.correlation_id import get_correlation_id
from shared_kernel.observability.request_id import get_request_id

from app.core.datetime_utils import to_iso_utc



@dataclass
class AuditContext:
    actor: str
    action: str
    resource: str
    correlation_id: str
    request_id: str
    timestamp: str
    tenant_id: str | None = None
    network_id: str | None = None
    locker_id: str | None = None

    @classmethod
    def now(
        cls,
        actor: str,
        action: str,
        resource: str,
        tenant_id: str | None = None,
        network_id: str | None = None,
        locker_id: str | None = None,
    ) -> "AuditContext":
        return cls(
            actor=actor,
            action=action,
            resource=resource,
            correlation_id=get_correlation_id(),
            request_id=get_request_id(),
            timestamp=datetime.now(timezone.utc).isoformat(),
            tenant_id=tenant_id,
            network_id=network_id,
            locker_id=locker_id,
        )
