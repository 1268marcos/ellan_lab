from __future__ import annotations

import threading
import uuid
from datetime import datetime, timezone


_LOCK = threading.Lock()
_BATCH_BY_RECEIPT: dict[str, dict] = {}
_RECEIPT_BY_IDEMPOTENCY: dict[str, str] = {}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _derive_idempotency_key(payload: dict) -> str:
    explicit = str(payload.get("idempotency_key") or "").strip()
    if explicit:
        return explicit
    invoice_id = str(payload.get("invoice_id") or "").strip()
    order_id = str(payload.get("order_id") or "").strip()
    access_key = str(payload.get("access_key") or "").strip()
    return f"{invoice_id}|{order_id}|{access_key}"


def submit_svrs_issue_batch_stub(payload: dict) -> dict:
    idempotency_key = _derive_idempotency_key(payload)
    if not idempotency_key:
        raise ValueError("idempotency_key_missing")

    ready_after_polls = max(1, int(payload.get("ready_after_polls") or 1))
    invoice_id = str(payload.get("invoice_id") or "").strip()
    access_key_hint = str(payload.get("access_key") or "").strip() or f"svrs_batch_{uuid.uuid4().hex[:28]}"
    protocol_hint = str(payload.get("protocol_number") or "").strip() or f"svrs_batch_prot_{uuid.uuid4().hex[:20]}"

    with _LOCK:
        existing_receipt = _RECEIPT_BY_IDEMPOTENCY.get(idempotency_key)
        if existing_receipt:
            batch = _BATCH_BY_RECEIPT[existing_receipt]
            return {
                "provider_namespace": "svrs_batch_stub",
                "batch_status": "RECEIVED",
                "receipt_number": existing_receipt,
                "idempotency_key": idempotency_key,
                "idempotent_replay": True,
                "created_at": batch["created_at"],
                "ready_after_polls": batch["ready_after_polls"],
                "poll_count": batch["poll_count"],
            }

        receipt_number = f"svrs_batch_rec_{uuid.uuid4().hex[:20]}"
        batch = {
            "receipt_number": receipt_number,
            "idempotency_key": idempotency_key,
            "invoice_id": invoice_id or None,
            "created_at": _now_iso(),
            "poll_count": 0,
            "ready_after_polls": ready_after_polls,
            "final_result": {
                "provider_namespace": "svrs_batch_stub",
                "provider_status": "AUTHORIZED",
                "provider_code": "100",
                "provider_message": "Autorizado em processamento assíncrono stub.",
                "receipt_number": receipt_number,
                "protocol_number": protocol_hint,
                "access_key": access_key_hint,
            },
        }
        _BATCH_BY_RECEIPT[receipt_number] = batch
        _RECEIPT_BY_IDEMPOTENCY[idempotency_key] = receipt_number

    return {
        "provider_namespace": "svrs_batch_stub",
        "batch_status": "RECEIVED",
        "receipt_number": receipt_number,
        "idempotency_key": idempotency_key,
        "idempotent_replay": False,
        "created_at": batch["created_at"],
        "ready_after_polls": ready_after_polls,
        "poll_count": 0,
    }


def query_svrs_issue_batch_stub(receipt_number: str) -> dict:
    rec = str(receipt_number or "").strip()
    if not rec:
        raise ValueError("receipt_number_required")

    with _LOCK:
        batch = _BATCH_BY_RECEIPT.get(rec)
        if not batch:
            return {
                "provider_namespace": "svrs_batch_stub",
                "batch_status": "NOT_FOUND",
                "receipt_number": rec,
            }

        batch["poll_count"] = int(batch.get("poll_count") or 0) + 1
        polls = batch["poll_count"]
        ready_after = int(batch.get("ready_after_polls") or 1)
        if polls < ready_after:
            return {
                "provider_namespace": "svrs_batch_stub",
                "batch_status": "PROCESSING",
                "receipt_number": rec,
                "poll_count": polls,
                "ready_after_polls": ready_after,
                "idempotency_key": batch["idempotency_key"],
            }

        return {
            "provider_namespace": "svrs_batch_stub",
            "batch_status": "PROCESSED",
            "receipt_number": rec,
            "poll_count": polls,
            "ready_after_polls": ready_after,
            "idempotency_key": batch["idempotency_key"],
            "result": dict(batch["final_result"]),
        }


def reset_svrs_issue_batch_stub_state() -> dict:
    with _LOCK:
        receipts = len(_BATCH_BY_RECEIPT)
        keys = len(_RECEIPT_BY_IDEMPOTENCY)
        _BATCH_BY_RECEIPT.clear()
        _RECEIPT_BY_IDEMPOTENCY.clear()
    return {
        "ok": True,
        "cleared_receipts": receipts,
        "cleared_idempotency_keys": keys,
    }
