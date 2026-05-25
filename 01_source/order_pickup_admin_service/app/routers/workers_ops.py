from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.order_ops import (
    InventorySyncQueueListOut,
    InventorySyncQueueOut,
    LifecycleDeadlineListOut,
    WorkerDlqListOut,
    WorkerQueueStatsOut,
)
from app.services import worker_ops_service

router = APIRouter(tags=["workers-ops"])


@router.get("/workers/stats", response_model=WorkerQueueStatsOut)
def workers_stats(db: Session = Depends(get_db)) -> WorkerQueueStatsOut:
    return worker_ops_service.worker_queue_stats(db)


@router.get("/workers/lifecycle-deadlines", response_model=LifecycleDeadlineListOut)
def list_lifecycle_deadlines(
    status: str | None = Query(default=None),
    deadline_type: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> LifecycleDeadlineListOut:
    items, total = worker_ops_service.list_lifecycle_deadlines(
        db, status=status, deadline_type=deadline_type, limit=limit, offset=offset
    )
    return LifecycleDeadlineListOut(items=items, total=total)


@router.get("/workers/inventory-sync-queue", response_model=InventorySyncQueueListOut)
def list_inventory_sync(
    status: str | None = Query(default=None),
    marketplace: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> InventorySyncQueueListOut:
    items, total = worker_ops_service.list_inventory_sync_queue(
        db, status=status, marketplace=marketplace, limit=limit, offset=offset
    )
    return InventorySyncQueueListOut(items=items, total=total)


@router.post("/workers/inventory-sync-queue/{queue_id}/replay", response_model=InventorySyncQueueOut)
def replay_inventory_sync(queue_id: str, db: Session = Depends(get_db)) -> InventorySyncQueueOut:
    return worker_ops_service.replay_inventory_sync(db, queue_id)


@router.get("/workers/dead-letter-queue", response_model=WorkerDlqListOut)
def list_worker_dlq(
    worker_name: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> WorkerDlqListOut:
    items, total = worker_ops_service.list_worker_dlq(
        db, worker_name=worker_name, limit=limit, offset=offset
    )
    return WorkerDlqListOut(items=items, total=total)
