"""POST assíncrono para webhook central quando o estado de um slot (door_state) muda."""

from __future__ import annotations

import json
import logging
import threading
from typing import Any, Optional

import requests

from app.core.config import settings

logger = logging.getLogger(__name__)


def _post_payload(url: str, headers: dict[str, str], body: dict[str, Any]) -> None:
    try:
        r = requests.post(
            url,
            headers=headers,
            data=json.dumps(body),
            timeout=float(settings.slot_state_webhook_timeout_sec or 2),
        )
        if not r.ok:
            logger.warning(
                "slot_state_webhook http_error status=%s body=%s",
                r.status_code,
                (r.text or "")[:500],
            )
    except Exception:
        logger.exception("slot_state_webhook request failed")


def notify_slot_state_change_async(
    *,
    locker_id: str,
    slot_label: str,
    previous_state: Optional[str],
    current_state: str,
    occurred_at: str,
    allocation_id: Optional[str] = None,
) -> None:
    url = (settings.slot_state_webhook_url or "").strip()
    if not url:
        return

    body: dict[str, Any] = {
        "locker_id": str(locker_id).strip().upper(),
        "slot_label": str(slot_label),
        "previous_state": previous_state,
        "current_state": str(current_state),
        "occurred_at": occurred_at,
        "allocation_id": allocation_id,
    }
    headers = {"Content-Type": "application/json"}
    sec = (settings.slot_state_webhook_secret or "").strip()
    if sec:
        headers["X-Webhook-Secret"] = sec

    threading.Thread(
        target=_post_payload,
        kwargs={"url": url, "headers": headers, "body": body},
        daemon=True,
        name="slot_state_webhook",
    ).start()
