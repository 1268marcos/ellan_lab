from __future__ import annotations

import socket
import time
import urllib.error
import urllib.request
import os
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.db import SessionLocal, init_db
from app.models.partner_integration_health import PartnerIntegrationHealth
from app.models.partner_webhook_endpoint import PartnerWebhookEndpoint
from app.services.ops_audit_service import record_ops_action_audit

POLL_SEC = int(os.getenv("PARTNER_INTEGRATION_HEALTH_POLL_SEC", "300"))
HTTP_TIMEOUT_SEC = float(os.getenv("PARTNER_INTEGRATION_HEALTH_TIMEOUT_SEC", "8"))
BATCH_SIZE = int(os.getenv("PARTNER_INTEGRATION_HEALTH_BATCH_SIZE", "500"))

_ALERT_STATUSES = {"DOWN", "DEGRADED", "TIMEOUT"}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _probe_endpoint(url: str) -> tuple[str, int | None, int | None, str | None]:
    started = time.monotonic()
    request = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SEC) as response:
            latency_ms = int((time.monotonic() - started) * 1000)
            http_status = int(response.status)
            if 200 <= http_status < 300:
                return "UP", latency_ms, http_status, None
            if 300 <= http_status < 500:
                return "DEGRADED", latency_ms, http_status, f"HTTP_{http_status}"
            return "DOWN", latency_ms, http_status, f"HTTP_{http_status}"
    except urllib.error.HTTPError as exc:
        latency_ms = int((time.monotonic() - started) * 1000)
        status_code = int(getattr(exc, "code", 0) or 0) or None
        if status_code is not None and 300 <= status_code < 500:
            return "DEGRADED", latency_ms, status_code, f"HTTP_{status_code}"
        return "DOWN", latency_ms, status_code, f"HTTP_{status_code or 'ERROR'}"
    except (urllib.error.URLError, TimeoutError, socket.timeout):
        latency_ms = int((time.monotonic() - started) * 1000)
        return "TIMEOUT", latency_ms, None, "TIMEOUT"
    except Exception as exc:
        latency_ms = int((time.monotonic() - started) * 1000)
        return "DOWN", latency_ms, None, str(exc)[:500]


def _audit_alert(
    *,
    db: Session,
    partner_id: str,
    endpoint_id: str,
    endpoint_url: str,
    status: str,
    latency_ms: int | None,
    http_status: int | None,
    error_message: str | None,
) -> None:
    record_ops_action_audit(
        db=db,
        action="PARTNER_HEALTH_CHECK_AUTO_ALERT",
        result="ERROR",
        correlation_id=f"health-auto-{uuid4().hex}",
        user_id=None,
        role="system_worker",
        error_message=error_message,
        details={
            "partner_id": partner_id,
            "endpoint_id": endpoint_id,
            "endpoint_url": endpoint_url,
            "status": status,
            "latency_ms": latency_ms,
            "http_status": http_status,
            "source": "partner_integration_health_worker",
        },
    )


def run_partner_integration_health_once(db: Session) -> None:
    endpoints = (
        db.query(PartnerWebhookEndpoint)
        .filter(
            PartnerWebhookEndpoint.partner_type == "ECOMMERCE",
            PartnerWebhookEndpoint.active.is_(True),
        )
        .order_by(PartnerWebhookEndpoint.updated_at.desc(), PartnerWebhookEndpoint.id.desc())
        .limit(BATCH_SIZE)
        .all()
    )
    now = _utcnow()
    for endpoint in endpoints:
        status, latency_ms, http_status, error_message = _probe_endpoint(endpoint.url)
        db.add(
            PartnerIntegrationHealth(
                partner_id=endpoint.partner_id,
                partner_type="ECOMMERCE",
                endpoint_url=endpoint.url,
                checked_at=now,
                status=status,
                latency_ms=latency_ms,
                http_status=http_status,
                error_message=error_message,
            )
        )
        if status in _ALERT_STATUSES:
            _audit_alert(
                db=db,
                partner_id=endpoint.partner_id,
                endpoint_id=endpoint.id,
                endpoint_url=endpoint.url,
                status=status,
                latency_ms=latency_ms,
                http_status=http_status,
                error_message=error_message,
            )
    db.commit()


def main() -> None:
    init_db()
    while True:
        db = SessionLocal()
        try:
            run_partner_integration_health_once(db)
        except Exception:
            db.rollback()
        finally:
            db.close()
        time.sleep(POLL_SEC)


if __name__ == "__main__":
    main()
