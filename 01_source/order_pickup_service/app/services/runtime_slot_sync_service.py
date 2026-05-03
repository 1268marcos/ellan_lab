"""Reconciliação locker_slots (Postgres) a partir do estado de hardware no runtime."""

from __future__ import annotations

import json
import logging
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.clients import runtime_client
from app.models.runtime_sync import RuntimeSyncQueue

logger = logging.getLogger(__name__)


def _backoff_delay_seconds(retry_count_after_increment: int) -> int:
    """Próximo atraso = min(2^retry_count, 3600) segundos; retry_count >= 1."""
    rc = int(max(1, retry_count_after_increment))
    return min(2**rc, 3600)


def map_runtime_state_to_pg_status(runtime_state: str) -> str:
    s = str(runtime_state or "").strip().upper()
    if s in ("AVAILABLE",):
        return "AVAILABLE"
    if s in ("OCCUPIED", "RESERVED", "PAID_PENDING_PICKUP"):
        return "OCCUPIED"
    if s in ("MAINTENANCE", "BLOCKED"):
        return s if s == "MAINTENANCE" else "BLOCKED"
    if s in ("FAULT",):
        return "FAULT"
    if s in ("OUT_OF_STOCK",):
        return "AVAILABLE"
    return "AVAILABLE"


def _parse_slot_number(slot_label: str) -> int:
    raw = str(slot_label or "").strip()
    try:
        return int(raw)
    except ValueError:
        m = re.search(r"\d+", raw)
        if not m:
            raise ValueError(f"invalid slot_label: {slot_label!r}")
        return int(m.group(0))


def _slot_label_matches_runtime_slot(slot_label: str, rt_slot: int) -> bool:
    raw = str(slot_label or "").strip()
    try:
        return int(raw) == int(rt_slot)
    except ValueError:
        m = re.search(r"\d+", raw)
        if not m:
            return False
        try:
            return int(m.group(0)) == int(rt_slot)
        except ValueError:
            return False


def _load_pg_slots(db: Session, locker_id: str) -> list[dict[str, Any]]:
    rows = db.execute(
        text(
            """
            SELECT id, locker_id, slot_label, status, occupied_since, current_allocation_id
            FROM locker_slots
            WHERE locker_id = :lid
            """
        ),
        {"lid": locker_id},
    ).mappings().all()
    return [dict(r) for r in rows]


def _list_active_lockers(db: Session) -> list[dict[str, Any]]:
    """
    Lockers ativos no cadastro central.
    (runtime_lockers.runtime_enabled vive no SQLite do runtime; aqui usamos `lockers.active`.)
    """
    rows = db.execute(
        text(
            """
            SELECT id, region, machine_id
            FROM lockers
            WHERE active = TRUE
            ORDER BY id
            """
        )
    ).mappings().all()
    return [dict(r) for r in rows]


def compute_slot_divergences(db: Session, locker_id: str, region: Optional[str]) -> list[dict[str, Any]]:
    runtime_rows = runtime_client.get_slots(locker_id, region=region)
    pg_rows = _load_pg_slots(db, locker_id)
    out: list[dict[str, Any]] = []
    for rt in runtime_rows:
        slot_num = int(rt.get("slot") or 0)
        rt_st = map_runtime_state_to_pg_status(str(rt.get("state") or ""))
        match = next((p for p in pg_rows if _slot_label_matches_runtime_slot(str(p.get("slot_label") or ""), slot_num)), None)
        if not match:
            out.append(
                {
                    "slot": slot_num,
                    "reason": "NO_PG_ROW",
                    "runtime_state": rt.get("state"),
                    "pg_status": None,
                }
            )
            continue
        pg_st = str(match.get("status") or "").strip().upper()
        if pg_st != rt_st:
            out.append(
                {
                    "slot": slot_num,
                    "slot_label": match.get("slot_label"),
                    "runtime_state": rt.get("state"),
                    "mapped_runtime": rt_st,
                    "pg_status": pg_st,
                    "current_allocation_id": match.get("current_allocation_id"),
                }
            )
    return out


def apply_slot_state_change_webhook(
    db: Session,
    *,
    locker_id: str,
    slot_label: str,
    current_state: str,
    previous_state: Optional[str] = None,
    occurred_at: Optional[str] = None,
    allocation_id: Optional[str] = None,
) -> dict[str, Any]:
    """
    Atualiza uma linha em locker_slots a partir do payload do runtime (webhook).
    Registra runtime_sync_queue com status WEBHOOK_TRIGGERED para auditoria.
    """
    locker_id = str(locker_id or "").strip().upper()
    try:
        slot_num = _parse_slot_number(slot_label)
    except ValueError as exc:
        return {"ok": False, "error": "INVALID_SLOT_LABEL", "message": str(exc)}

    target_status = map_runtime_state_to_pg_status(current_state)
    pg_rows = _load_pg_slots(db, locker_id)
    match = next(
        (p for p in pg_rows if _slot_label_matches_runtime_slot(str(p.get("slot_label") or ""), slot_num)),
        None,
    )
    if not match:
        return {"ok": False, "error": "SLOT_NOT_FOUND", "locker_id": locker_id, "slot_label": slot_label}

    now = datetime.now(timezone.utc)
    cur_status = str(match.get("status") or "").strip().upper()
    occ = match.get("occupied_since")
    alloc_id = match.get("current_allocation_id")

    if target_status == "AVAILABLE":
        alloc_id = None
        occ = None
    elif target_status == "OCCUPIED":
        if allocation_id:
            alloc_id = str(allocation_id).strip() or None
        if occ is None:
            occ = now

    res = db.execute(
        text(
            """
            UPDATE locker_slots
            SET status = :st,
                occupied_since = :occ,
                current_allocation_id = :aid,
                updated_at = :now
            WHERE id = :sid
            """
        ),
        {
            "st": target_status,
            "occ": occ,
            "aid": alloc_id,
            "now": now,
            "sid": str(match["id"]),
        },
    )
    rows_touched = int(res.rowcount or 0)

    qid = str(uuid.uuid4())
    audit = json.dumps(
        {
            "source": "runtime_webhook",
            "previous_state": previous_state,
            "current_state": current_state,
            "occurred_at": occurred_at,
            "mapped_status": target_status,
            "prior_pg_status": cur_status,
        },
        ensure_ascii=False,
    )[:7999]
    db.add(
        RuntimeSyncQueue(
            id=qid,
            locker_id=locker_id,
            operation="WEBHOOK_SLOT_STATE",
            status="WEBHOOK_TRIGGERED",
            retry_count=0,
            max_retries=3,
            last_error=audit,
            created_at=now,
            updated_at=now,
            processed_at=now,
            next_retry_at=None,
        )
    )
    db.commit()
    return {
        "ok": True,
        "locker_id": locker_id,
        "slot_label": str(match.get("slot_label") or slot_label),
        "queue_id": qid,
        "mapped_status": target_status,
        "rows_updated": rows_touched,
    }


def sync_locker_slots_from_runtime(
    db: Session,
    locker_id: str,
    region: Optional[str] = None,
    *,
    existing_queue_id: Optional[str] = None,
) -> dict[str, Any]:
    """
    GET runtime slots, compara com locker_slots e aplica UPDATEs nas divergências de status.
    Registra ou atualiza runtime_sync_queue. Com existing_queue_id, assume fila PENDING e faz claim PROCESSING.
    """
    locker_id = str(locker_id or "").strip().upper()
    now = datetime.now(timezone.utc)
    qid = str(uuid.uuid4())
    updated = 0
    divergences_before = 0
    divergences_after = 0
    runtime_len = 0

    if existing_queue_id:
        res = db.execute(
            text(
                """
                UPDATE runtime_sync_queue
                SET status = 'PROCESSING', updated_at = :n
                WHERE id = :qid
                  AND operation = 'SYNC_SLOTS'
                  AND status = 'PENDING'
                  AND (next_retry_at IS NULL OR next_retry_at <= :n)
                """
            ),
            {"qid": str(existing_queue_id), "n": now},
        )
        if (res.rowcount or 0) != 1:
            db.rollback()
            return {
                "ok": False,
                "locker_id": locker_id,
                "skipped": True,
                "reason": "queue_item_not_claimable",
                "queue_id": str(existing_queue_id),
            }

    try:
        runtime_rows = runtime_client.get_slots(locker_id, region=region)
        runtime_len = len(runtime_rows)
        pg_rows = _load_pg_slots(db, locker_id)
        divergences_before = len(compute_slot_divergences(db, locker_id, region))

        for rt in runtime_rows:
            slot_num = int(rt.get("slot") or 0)
            target_status = map_runtime_state_to_pg_status(str(rt.get("state") or ""))
            match = next(
                (p for p in pg_rows if _slot_label_matches_runtime_slot(str(p.get("slot_label") or ""), slot_num)),
                None,
            )
            if not match:
                continue
            cur_status = str(match.get("status") or "").strip().upper()
            if cur_status == target_status:
                continue

            occ = match.get("occupied_since")
            alloc_id = match.get("current_allocation_id")

            if target_status == "AVAILABLE":
                alloc_id = None
                occ = None
            elif target_status == "OCCUPIED" and occ is None:
                occ = now

            db.execute(
                text(
                    """
                    UPDATE locker_slots
                    SET status = :st,
                        occupied_since = :occ,
                        current_allocation_id = :aid,
                        updated_at = :now
                    WHERE id = :sid
                    """
                ),
                {
                    "st": target_status,
                    "occ": occ,
                    "aid": alloc_id,
                    "now": now,
                    "sid": str(match["id"]),
                },
            )
            updated += 1
            match["status"] = target_status
            match["occupied_since"] = occ
            match["current_allocation_id"] = alloc_id

        done = datetime.now(timezone.utc)
        if existing_queue_id:
            db.execute(
                text(
                    """
                    UPDATE runtime_sync_queue
                    SET status = 'SUCCESS',
                        processed_at = :d,
                        updated_at = :d,
                        next_retry_at = NULL,
                        last_error = NULL
                    WHERE id = :qid
                    """
                ),
                {"d": done, "qid": str(existing_queue_id)},
            )
        else:
            db.add(
                RuntimeSyncQueue(
                    id=qid,
                    locker_id=locker_id,
                    operation="SYNC_SLOTS",
                    status="SUCCESS",
                    retry_count=0,
                    max_retries=3,
                    last_error=None,
                    created_at=done,
                    updated_at=done,
                    processed_at=done,
                    next_retry_at=None,
                )
            )
        db.commit()
        divergences_after = len(compute_slot_divergences(db, locker_id, region))
        return {
            "ok": True,
            "locker_id": locker_id,
            "queue_id": str(existing_queue_id or qid),
            "runtime_slots": runtime_len,
            "updated_rows": updated,
            "divergences_before": divergences_before,
            "divergences_after": divergences_after,
        }
    except Exception as exc:
        err = str(exc)
        logger.exception("runtime slot sync failed locker_id=%s", locker_id)
        db.rollback()
        fail_at = datetime.now(timezone.utc)
        try:
            if existing_queue_id:
                qrow = db.execute(
                    text("SELECT retry_count, max_retries FROM runtime_sync_queue WHERE id = :id LIMIT 1"),
                    {"id": str(existing_queue_id)},
                ).mappings().first()
                new_rc = int(qrow["retry_count"] or 0) + 1 if qrow else 1
                max_r = int(qrow["max_retries"] or 3) if qrow else 3
                delay = _backoff_delay_seconds(new_rc)
                next_at = fail_at + timedelta(seconds=delay)
                err_trunc = err[:8000] if err else "error"
                if new_rc > max_r:
                    db.execute(
                        text(
                            """
                            UPDATE runtime_sync_queue
                            SET status = 'FAILED',
                                retry_count = :rc,
                                last_error = :err,
                                processed_at = :ft,
                                updated_at = :ft,
                                next_retry_at = NULL
                            WHERE id = :qid
                            """
                        ),
                        {"rc": new_rc, "err": err_trunc, "ft": fail_at, "qid": str(existing_queue_id)},
                    )
                else:
                    db.execute(
                        text(
                            """
                            UPDATE runtime_sync_queue
                            SET status = 'PENDING',
                                retry_count = :rc,
                                last_error = :err,
                                processed_at = NULL,
                                updated_at = :ft,
                                next_retry_at = :nxt
                            WHERE id = :qid
                            """
                        ),
                        {"rc": new_rc, "err": err_trunc, "ft": fail_at, "nxt": next_at, "qid": str(existing_queue_id)},
                    )
            else:
                fail_id = str(uuid.uuid4())
                next_at = fail_at + timedelta(seconds=_backoff_delay_seconds(1))
                db.add(
                    RuntimeSyncQueue(
                        id=fail_id,
                        locker_id=locker_id,
                        operation="SYNC_SLOTS",
                        status="PENDING",
                        retry_count=1,
                        max_retries=3,
                        last_error=err[:8000] if err else "error",
                        created_at=fail_at,
                        updated_at=fail_at,
                        processed_at=None,
                        next_retry_at=next_at,
                    )
                )
            db.commit()
        except Exception:
            logger.exception("failed to persist runtime_sync_queue failure row")
            db.rollback()
        fail_qid = str(existing_queue_id) if existing_queue_id else fail_id
        return {
            "ok": False,
            "locker_id": locker_id,
            "queue_id": fail_qid,
            "error": err,
            "updated_rows": updated,
            "runtime_slots": runtime_len,
            "divergences_before": divergences_before,
        }


def process_ready_runtime_sync_queue_batch(db: Session, *, batch_limit: int = 8) -> int:
    """Processa itens SYNC_SLOTS em PENDING com next_retry_at <= agora (ou NULL)."""
    rows = db.execute(
        text(
            """
            SELECT id, locker_id
            FROM runtime_sync_queue
            WHERE operation = 'SYNC_SLOTS'
              AND status = 'PENDING'
              AND (next_retry_at IS NULL OR next_retry_at <= NOW())
            ORDER BY next_retry_at NULLS FIRST, created_at ASC
            LIMIT :lim
            """
        ),
        {"lim": int(batch_limit)},
    ).mappings().all()
    processed = 0
    for r in rows:
        qid = str(r["id"])
        lid = str(r["locker_id"])
        reg = db.execute(
            text("SELECT region FROM lockers WHERE id = :id LIMIT 1"),
            {"id": lid},
        ).mappings().first()
        region = str(reg.get("region") or "").strip() or None if reg else None
        try:
            out = sync_locker_slots_from_runtime(db, lid, region=region, existing_queue_id=qid)
            if not out.get("skipped"):
                processed += 1
        except Exception:
            logger.exception("runtime_sync queue item failed queue_id=%s locker_id=%s", qid, lid)
    return processed


def retry_runtime_sync_queue_item_by_id(db: Session, queue_id: str) -> dict[str, Any]:
    """OPS: re-enfileira e executa imediatamente um item SYNC_SLOTS."""
    qid = str(queue_id or "").strip()
    row = db.execute(
        text("SELECT id, locker_id, operation, status FROM runtime_sync_queue WHERE id = :id LIMIT 1"),
        {"id": qid},
    ).mappings().first()
    if not row or str(row.get("operation") or "") != "SYNC_SLOTS":
        raise ValueError("QUEUE_ITEM_NOT_FOUND")
    if str(row.get("status") or "").upper() == "SUCCESS":
        raise ValueError("ALREADY_SUCCESS")
    lid = str(row["locker_id"])
    now = datetime.now(timezone.utc)
    db.execute(
        text(
            """
            UPDATE runtime_sync_queue
            SET status = 'PENDING',
                next_retry_at = :n,
                processed_at = NULL,
                updated_at = :n
            WHERE id = :id
            """
        ),
        {"id": qid, "n": now},
    )
    db.commit()
    reg = db.execute(text("SELECT region FROM lockers WHERE id = :id LIMIT 1"), {"id": lid}).mappings().first()
    region = str(reg.get("region") or "").strip() or None if reg else None
    return sync_locker_slots_from_runtime(db, lid, region=region, existing_queue_id=qid)


def sync_all_active_lockers(db: Session) -> dict[str, Any]:
    lockers = _list_active_lockers(db)
    results: list[dict[str, Any]] = []
    ok = 0
    failed = 0
    for lk in lockers:
        lid = str(lk["id"])
        region = str(lk.get("region") or "") or None
        r = sync_locker_slots_from_runtime(db, lid, region=region)
        results.append(r)
        if r.get("ok"):
            ok += 1
        else:
            failed += 1
    return {"ok": failed == 0, "processed": len(results), "success": ok, "failed": failed, "results": results}


def fetch_queue_status(db: Session, *, pending_limit: int = 100) -> dict[str, Any]:
    pending = db.execute(
        text(
            """
            SELECT id, locker_id, operation, status, retry_count, last_error, created_at, updated_at, processed_at, next_retry_at
            FROM runtime_sync_queue
            WHERE status IN ('PENDING', 'PROCESSING')
            ORDER BY created_at DESC
            LIMIT :lim
            """
        ),
        {"lim": int(pending_limit)},
    ).mappings().all()

    last_by = db.execute(
        text(
            """
            SELECT q.locker_id, q.status, q.processed_at, q.created_at, q.operation
            FROM runtime_sync_queue q
            INNER JOIN (
              SELECT locker_id, MAX(processed_at) AS mx
              FROM runtime_sync_queue
              WHERE operation = 'SYNC_SLOTS' AND processed_at IS NOT NULL
              GROUP BY locker_id
            ) t ON q.locker_id = t.locker_id
              AND q.processed_at = t.mx
              AND q.operation = 'SYNC_SLOTS'
            """
        )
    ).mappings().all()

    return {
        "pending": [dict(r) for r in pending],
        "last_by_locker": [dict(r) for r in last_by],
    }


def divergences_report(db: Session) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for lk in _list_active_lockers(db):
        lid = str(lk["id"])
        region = str(lk.get("region") or "") or None
        try:
            divs = compute_slot_divergences(db, lid, region)
        except Exception as exc:
            out.append(
                {
                    "locker_id": lid,
                    "region": region,
                    "divergences_count": -1,
                    "error": str(exc),
                    "items": [],
                }
            )
            continue
        out.append(
            {
                "locker_id": lid,
                "region": region,
                "divergences_count": len(divs),
                "items": divs[:200],
            }
        )
    return out
