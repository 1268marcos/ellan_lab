from __future__ import annotations

import time
from typing import Optional

from fastapi import APIRouter, Query

# from app.core.config import GATEWAY_ID, GATEWAY_LOG_DIR, LOG_HASH_SALT
from app.core.config import settings

from app.core.event_log import GatewayEventLogger

router = APIRouter()


@router.get("/audit/log/verify")
def verify_log(date: str = Query(..., description="YYYY-MM-DD")):
    """
    01_source/payment_gateway/app/routers/audit_log.py

    Não aponta para a pasta correta - VERIFICAR
    """
    logger = GatewayEventLogger(
        gateway_id=settings.GATEWAY_ID,
        log_dir=settings.GATEWAY_LOG_DIR,
        log_hash_salt=settings.LOG_HASH_SALT,
    )
    res = logger.verify_chain(date)
    return {
        "service": "payment_gateway",
        "endpoint": "/audit/log/verify",
        "timestamp": time.time(),
        **res,
    }


@router.get("/audit/log/tail")
def tail_log(
    date: str = Query(..., description="YYYY-MM-DD"),
    n: int = Query(50, ge=1, le=500),
):
    logger = GatewayEventLogger(
        gateway_id=settings.GATEWAY_ID,
        log_dir=settings.GATEWAY_LOG_DIR,
        log_hash_salt=settings.LOG_HASH_SALT,
    )
    path = logger.log_path_for_date(date)

    lines = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for ln in f:
                ln = ln.strip()
                if ln:
                    lines.append(ln)
        lines = lines[-n:]
        items = []
        for ln in lines:
            try:
                import json
                items.append(json.loads(ln))
            except Exception:
                items.append({"raw": ln})
    except FileNotFoundError:
        items = []

    return {
        "service": "payment_gateway",
        "endpoint": "/audit/log/tail",
        "timestamp": time.time(),
        "date": date,
        "path": path,
        "count": len(items),
        "items": items,
    }