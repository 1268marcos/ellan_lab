from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.schemas.order_ops import (
    InventorySyncQueueOut,
    LifecycleDeadlineOut,
    WorkerDlqOut,
    WorkerQueueStatsOut,
)


def _table_exists(db: Session, table_name: str) -> bool:
    row = db.execute(
        text(
            """
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = :t LIMIT 1
            """
        ),
        {"t": table_name},
    ).first()
    return row is not None


def _count_by_status(db: Session, table: str, status_col: str = "status") -> dict[str, int]:
    if not _table_exists(db, table):
        return {}
    rows = db.execute(
        text(f"SELECT {status_col} AS st, COUNT(*)::int AS c FROM {table} GROUP BY {status_col}")
    ).mappings().all()
    return {str(r["st"]): int(r["c"]) for r in rows}


def worker_queue_stats(db: Session) -> WorkerQueueStatsOut:
    return WorkerQueueStatsOut(
        domain_event_outbox=_count_by_status(db, "domain_event_outbox"),
        lifecycle_deadlines=_count_by_status(db, "lifecycle_deadlines"),
        inventory_sync_queue=_count_by_status(db, "inventory_sync_queue"),
        worker_dead_letter_queue=_count_by_status(db, "worker_dead_letter_queue", "worker_name"),
    )


def list_lifecycle_deadlines(
    db: Session,
    *,
    status: str | None = None,
    deadline_type: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[LifecycleDeadlineOut], int]:
    if not _table_exists(db, "lifecycle_deadlines"):
        return [], 0
    clauses = ["1=1"]
    params: dict = {"limit": limit, "offset": offset}
    if status:
        clauses.append("status = :status")
        params["status"] = status.upper()
    if deadline_type:
        clauses.append("deadline_type::text = :dtype")
        params["dtype"] = deadline_type.upper()
    where = " AND ".join(clauses)
    total = db.execute(
        text(f"SELECT COUNT(*)::int FROM lifecycle_deadlines WHERE {where}"), params
    ).scalar_one()
    rows = db.execute(
        text(
            f"""
            SELECT id::text, deadline_key, order_id, deadline_type::text AS deadline_type,
                   status::text AS status, due_at, failure_count, created_at
            FROM lifecycle_deadlines WHERE {where}
            ORDER BY due_at ASC OFFSET :offset LIMIT :limit
            """
        ),
        params,
    ).mappings().all()
    return [LifecycleDeadlineOut.model_validate(dict(r)) for r in rows], int(total)


def list_inventory_sync_queue(
    db: Session,
    *,
    status: str | None = None,
    marketplace: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[InventorySyncQueueOut], int]:
    if not _table_exists(db, "inventory_sync_queue"):
        return [], 0
    clauses = ["1=1"]
    params: dict = {"limit": limit, "offset": offset}
    if status:
        clauses.append("status = :status")
        params["status"] = status.upper()
    if marketplace:
        clauses.append("marketplace = :marketplace")
        params["marketplace"] = marketplace.upper()
    where = " AND ".join(clauses)
    total = db.execute(
        text(f"SELECT COUNT(*)::int FROM inventory_sync_queue WHERE {where}"), params
    ).scalar_one()
    rows = db.execute(
        text(
            f"""
            SELECT id, product_id, marketplace, status, quantity_available,
                   retry_count, last_error, created_at
            FROM inventory_sync_queue WHERE {where}
            ORDER BY created_at DESC OFFSET :offset LIMIT :limit
            """
        ),
        params,
    ).mappings().all()
    return [InventorySyncQueueOut.model_validate(dict(r)) for r in rows], int(total)


def replay_inventory_sync(db: Session, queue_id: str) -> InventorySyncQueueOut:
    if not _table_exists(db, "inventory_sync_queue"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="inventory_sync_queue_not_found")
    row = db.execute(
        text("SELECT id FROM inventory_sync_queue WHERE id = :id"), {"id": queue_id}
    ).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="inventory_sync_item_not_found")
    db.execute(
        text(
            """
            UPDATE inventory_sync_queue
            SET status = 'PENDING', retry_count = 0, last_error = NULL,
                next_retry_at = NULL, processing_started_at = NULL, updated_at = NOW()
            WHERE id = :id
            """
        ),
        {"id": queue_id},
    )
    db.commit()
    refreshed = db.execute(
        text(
            """
            SELECT id, product_id, marketplace, status, quantity_available,
                   retry_count, last_error, created_at
            FROM inventory_sync_queue WHERE id = :id
            """
        ),
        {"id": queue_id},
    ).mappings().first()
    return InventorySyncQueueOut.model_validate(dict(refreshed))


def list_worker_dlq(
    db: Session,
    *,
    worker_name: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[WorkerDlqOut], int]:
    if not _table_exists(db, "worker_dead_letter_queue"):
        return [], 0
    clauses = ["1=1"]
    params: dict = {"limit": limit, "offset": offset}
    if worker_name:
        clauses.append("worker_name = :worker_name")
        params["worker_name"] = worker_name
    where = " AND ".join(clauses)
    total = db.execute(
        text(f"SELECT COUNT(*)::int FROM worker_dead_letter_queue WHERE {where}"), params
    ).scalar_one()
    rows = db.execute(
        text(
            f"""
            SELECT id, worker_name, source_table, source_id, error_message,
                   attempt_count, dead_lettered_at
            FROM worker_dead_letter_queue WHERE {where}
            ORDER BY dead_lettered_at DESC OFFSET :offset LIMIT :limit
            """
        ),
        params,
    ).mappings().all()
    return [WorkerDlqOut.model_validate(dict(r)) for r in rows], int(total)
