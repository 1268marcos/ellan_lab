from __future__ import annotations

import hashlib
import hmac
import json
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.order_fulfillment_tracking_service import upsert_order_fulfillment_tracking
from app.services.ops_audit_service import record_ops_action_audit

_OUTBOX_STATUSES_RETRY = {"PENDING", "FAILED"}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _next_retry_at(attempt_count: int, base_backoff_sec: int) -> datetime:
    multiplier = max(1, 2 ** max(0, attempt_count - 1))
    delay_sec = min(base_backoff_sec * multiplier, 3600)
    return _utc_now() + timedelta(seconds=delay_sec)


def _json_load_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item or "").strip()]
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return [str(item) for item in parsed if str(item or "").strip()]
        except Exception:
            return []
    return []


def _json_load_dict(value: object) -> dict:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            return {}
    return {}


def _resolve_endpoint_for_event(db: Session, *, partner_id: str, event_type: str) -> dict | None:
    rows = db.execute(
        text(
            """
            SELECT id, url, secret_key, api_version, retry_policy, events_json
            FROM partner_webhook_endpoints
            WHERE partner_id = :partner_id
              AND partner_type = 'ECOMMERCE'
              AND active = TRUE
            ORDER BY created_at ASC, id ASC
            """
        ),
        {"partner_id": partner_id},
    ).mappings().all()
    normalized_event = str(event_type or "").strip().upper()
    for row in rows:
        events = [str(item).strip().upper() for item in _json_load_list(row.get("events_json"))]
        if not events:
            continue
        if "*" in events or normalized_event in events:
            return dict(row)
    return None


def _build_signature(secret_key: str, payload_bytes: bytes) -> str:
    digest = hmac.new(secret_key.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def _deliver_to_partner(*, endpoint: dict, event_type: str, outbox_id: str, payload: dict) -> int:
    url = str(endpoint.get("url") or "").strip()
    if not url:
        raise RuntimeError("EMPTY_WEBHOOK_URL")
    payload_bytes = json.dumps(payload or {}, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=payload_bytes,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    secret = str(endpoint.get("secret_key") or "").strip()
    if secret:
        request.add_header("X-Ellan-Signature", _build_signature(secret, payload_bytes))
    request.add_header("X-Ellan-Event", str(event_type or "ORDER_EVENT"))
    request.add_header("X-Ellan-Event-Id", outbox_id)
    request.add_header("X-Ellan-Api-Version", str(endpoint.get("api_version") or "v1"))
    with urllib.request.urlopen(request, timeout=8.0) as response:
        return int(response.status)


def run_integration_order_events_outbox_once(
    db: Session,
    *,
    batch_size: int = 50,
    max_attempts: int = 5,
    base_backoff_sec: int = 30,
) -> dict[str, int]:
    now = _utc_now()
    batch_size = max(1, min(int(batch_size or 50), 500))
    max_attempts = max(1, min(int(max_attempts or 5), 20))
    base_backoff_sec = max(5, min(int(base_backoff_sec or 30), 3600))

    rows = db.execute(
        text(
            """
            SELECT id, order_id, partner_id, event_type, status, attempt_count
            FROM partner_order_events_outbox
            WHERE status IN ('PENDING','FAILED')
              AND COALESCE(next_retry_at, NOW()) <= :now
            ORDER BY created_at ASC, id ASC
            LIMIT :limit
            """
        ),
        {"now": now, "limit": batch_size},
    ).mappings().all()

    scanned = len(rows)
    delivered = 0
    failed = 0
    dead_letter = 0
    skipped = 0

    for row in rows:
        outbox_id = str(row.get("id") or "")
        order_id = str(row.get("order_id") or "")
        partner_id = str(row.get("partner_id") or "")
        event_type = str(row.get("event_type") or "")
        payload = _json_load_dict(row.get("payload_json"))
        attempts_before = int(row.get("attempt_count") or 0)
        next_attempt = attempts_before + 1

        endpoint = _resolve_endpoint_for_event(db, partner_id=partner_id, event_type=event_type)
        if endpoint is None:
            db.execute(
                text(
                    """
                    UPDATE partner_order_events_outbox
                    SET status = 'SKIPPED',
                        attempt_count = :attempt_count,
                        next_retry_at = NULL,
                        last_error = :last_error,
                        updated_at = NOW()
                    WHERE id = :id
                    """
                ),
                {
                    "id": outbox_id,
                    "attempt_count": next_attempt,
                    "last_error": "PARTNER_WEBHOOK_ENDPOINT_NOT_FOUND",
                },
            )
            skipped += 1
            upsert_order_fulfillment_tracking(
                db,
                order_id=order_id,
                partner_id=partner_id,
                event_type=event_type,
                outbox_status="SKIPPED",
            )
            record_ops_action_audit(
                db=db,
                action="I1_OUTBOX_ENDPOINT_MISSING",
                result="ERROR",
                correlation_id=f"corr-i1-endpoint-missing-{outbox_id}",
                role="system",
                order_id=order_id or None,
                error_message="PARTNER_WEBHOOK_ENDPOINT_NOT_FOUND",
                details={
                    "outbox_id": outbox_id,
                    "partner_id": partner_id,
                    "event_type": event_type,
                    "attempt_count": next_attempt,
                },
            )
            continue

        endpoint_policy = _json_load_dict(endpoint.get("retry_policy"))
        endpoint_max_attempts = max(1, min(int(endpoint_policy.get("max_attempts") or max_attempts), 20))
        endpoint_backoff_sec = max(5, min(int(endpoint_policy.get("backoff_sec") or base_backoff_sec), 3600))

        try:
            http_status = _deliver_to_partner(
                endpoint=endpoint,
                event_type=event_type,
                outbox_id=outbox_id,
                payload=payload,
            )
            if 200 <= http_status < 300:
                db.execute(
                    text(
                        """
                        UPDATE partner_order_events_outbox
                        SET status = 'DELIVERED',
                            attempt_count = :attempt_count,
                            delivered_at = NOW(),
                            next_retry_at = NULL,
                            last_error = NULL,
                            updated_at = NOW()
                        WHERE id = :id
                        """
                    ),
                    {"id": outbox_id, "attempt_count": next_attempt},
                )
                delivered += 1
                upsert_order_fulfillment_tracking(
                    db,
                    order_id=order_id,
                    partner_id=partner_id,
                    event_type=event_type,
                    outbox_status="DELIVERED",
                )
                record_ops_action_audit(
                    db=db,
                    action="I1_OUTBOX_DELIVERED",
                    result="SUCCESS",
                    correlation_id=f"corr-i1-delivery-{outbox_id}",
                    role="system",
                    order_id=order_id or None,
                    details={
                        "outbox_id": outbox_id,
                        "partner_id": partner_id,
                        "event_type": event_type,
                        "attempt_count": next_attempt,
                        "endpoint_id": str(endpoint.get("id") or ""),
                        "endpoint_url": str(endpoint.get("url") or ""),
                        "http_status": http_status,
                    },
                )
                continue
            error_message = f"HTTP_{http_status}"
        except urllib.error.HTTPError as exc:
            error_message = f"HTTP_ERROR_{int(getattr(exc, 'code', 0) or 0)}"
        except Exception as exc:
            error_message = str(exc)[:4000]

        if next_attempt >= endpoint_max_attempts:
            db.execute(
                text(
                    """
                    UPDATE partner_order_events_outbox
                    SET status = 'DEAD_LETTER',
                        attempt_count = :attempt_count,
                        next_retry_at = NULL,
                        last_error = :last_error,
                        updated_at = NOW()
                    WHERE id = :id
                    """
                ),
                {
                    "id": outbox_id,
                    "attempt_count": next_attempt,
                    "last_error": error_message,
                },
            )
            dead_letter += 1
            upsert_order_fulfillment_tracking(
                db,
                order_id=order_id,
                partner_id=partner_id,
                event_type=event_type,
                outbox_status="DEAD_LETTER",
            )
            record_ops_action_audit(
                db=db,
                action="I1_OUTBOX_DEAD_LETTER",
                result="ERROR",
                correlation_id=f"corr-i1-dead-{outbox_id}",
                role="system",
                order_id=order_id or None,
                error_message=error_message,
                details={
                    "outbox_id": outbox_id,
                    "partner_id": partner_id,
                    "event_type": event_type,
                    "attempt_count": next_attempt,
                    "max_attempts": endpoint_max_attempts,
                    "endpoint_id": str(endpoint.get("id") or ""),
                    "endpoint_url": str(endpoint.get("url") or ""),
                },
            )
            continue

        retry_at = _next_retry_at(next_attempt, endpoint_backoff_sec)
        db.execute(
            text(
                """
                UPDATE partner_order_events_outbox
                SET status = 'FAILED',
                    attempt_count = :attempt_count,
                    next_retry_at = :next_retry_at,
                    last_error = :last_error,
                    updated_at = NOW()
                WHERE id = :id
                """
            ),
            {
                "id": outbox_id,
                "attempt_count": next_attempt,
                "next_retry_at": retry_at,
                "last_error": error_message,
            },
        )
        failed += 1
        upsert_order_fulfillment_tracking(
            db,
            order_id=order_id,
            partner_id=partner_id,
            event_type=event_type,
            outbox_status="FAILED",
        )
        record_ops_action_audit(
            db=db,
            action="I1_OUTBOX_RETRY_SCHEDULED",
            result="ERROR",
            correlation_id=f"corr-i1-retry-{outbox_id}",
            role="system",
            order_id=order_id or None,
            error_message=error_message,
            details={
                "outbox_id": outbox_id,
                "partner_id": partner_id,
                "event_type": event_type,
                "attempt_count": next_attempt,
                "next_retry_at": retry_at.isoformat(),
                "max_attempts": endpoint_max_attempts,
                "base_backoff_sec": endpoint_backoff_sec,
                "endpoint_id": str(endpoint.get("id") or ""),
                "endpoint_url": str(endpoint.get("url") or ""),
            },
        )

    db.commit()
    return {
        "scanned": scanned,
        "delivered": delivered,
        "failed": failed,
        "dead_letter": dead_letter,
        "skipped": skipped,
    }
