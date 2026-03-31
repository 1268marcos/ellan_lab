# 01_source/payment_gateway/app/routers/audit_snapshot.py

from __future__ import annotations

import time
from fastapi import APIRouter, Query

"""
from app.core.config import (
    SQLITE_PATH,
    GATEWAY_ID,
    GATEWAY_LOG_DIR,
    LOG_HASH_SALT,
    ANTIFRAUD_PEPPER,
    SNAPSHOT_DIR,
    SNAPSHOT_BACKUP_DIR,
    DEVICE_FP_VERSION,
    IDEMPOTENCY_TTL_SEC,
)
"""
from app.core.config import settings

from app.core.hashing import sha256_prefixed
from app.core.event_log import GatewayEventLogger
from app.core.antifraud_snapshot import GatewaySnapshotService
from app.core.antifraud_snapshot_verify import verify_snapshot
from app.services.sqlite_service import SQLiteService

router = APIRouter()


def _pepper_fingerprint() -> str:
    return sha256_prefixed(settings.ANTIFRAUD_PEPPER)


def _config_fingerprint() -> str:
    # fingerprint estável da config ativa (não expõe segredo)
    base = f"{settings.GATEWAY_ID}::{settings.SQLITE_PATH}::{_pepper_fingerprint()}::{settings.DEVICE_FP_VERSION}::{settings.IDEMPOTENCY_TTL_SEC}"
    return sha256_prefixed(base)


@router.get("/audit/snapshot/daily")
def build_daily_snapshot(date: str = Query(..., description="YYYY-MM-DD")):
    sqlite = SQLiteService(settings.SQLITE_PATH)
    logger = GatewayEventLogger(gateway_id=settings.GATEWAY_ID, log_dir=settings.GATEWAY_LOG_DIR, log_hash_salt=settings.LOG_HASH_SALT)

    svc = GatewaySnapshotService(
        sqlite=sqlite,
        logger=logger,
        snapshots_dir=settings.SNAPSHOT_DIR,
        backups_dir=settings.SNAPSHOT_BACKUP_DIR,
        pepper_fingerprint=_pepper_fingerprint(),
        config_fingerprint=_config_fingerprint(),
    )

    res = svc.write_snapshot(date)
    snap = svc.read_snapshot(date)

    return {
        "service": "payment_gateway",
        "endpoint": "/audit/snapshot/daily",
        "timestamp": time.time(),
        "result": "ok",
        "write": res,
        "snapshot": snap,
    }


@router.post("/audit/snapshot/verify")
def verify_daily_snapshot(date: str = Query(..., description="YYYY-MM-DD")):
    sqlite = SQLiteService(settings.SQLITE_PATH)
    logger = GatewayEventLogger(gateway_id=settings.GATEWAY_ID, log_dir=settings.GATEWAY_LOG_DIR, log_hash_salt=settings.LOG_HASH_SALT)

    svc = GatewaySnapshotService(
        sqlite=sqlite,
        logger=logger,
        snapshots_dir=settings.SNAPSHOT_DIR,
        backups_dir=settings.SNAPSHOT_BACKUP_DIR,
        pepper_fingerprint=_pepper_fingerprint(),
        config_fingerprint=_config_fingerprint(),
    )

    snap = svc.read_snapshot(date)

    if not snap:
        return {
            "service": "payment_gateway",
            "endpoint": "/audit/snapshot/verify",
            "timestamp": time.time(),
            "ok": False,
            "status": "snapshot_missing",
            "date": date,
        }

    ver = verify_snapshot(
        snapshot=snap,
        logger=logger,
        expected_config_fingerprint=_config_fingerprint(),
    )

    return {
        "service": "payment_gateway",
        "endpoint": "/audit/snapshot/verify",
        "timestamp": time.time(),
        "date": date,
        **ver,
    }