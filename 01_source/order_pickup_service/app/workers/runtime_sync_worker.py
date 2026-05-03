"""Worker periódico: reconcilia locker_slots (Postgres) com GET /locker/slots no runtime."""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy import text

from app.core.config import settings
from app.core.db import SessionLocal, engine
from app.services import runtime_slot_sync_service as rss

logger = logging.getLogger(__name__)


def _is_postgres() -> bool:
    return engine.dialect.name == "postgresql"


async def runtime_sync_loop() -> None:
    interval = float(settings.runtime_slot_sync_poll_sec or 30)
    while True:
        if not settings.runtime_slot_sync_enabled:
            await asyncio.sleep(interval)
            continue
        if not _is_postgres():
            await asyncio.sleep(interval)
            continue
        db = SessionLocal()
        try:
            await asyncio.to_thread(_run_tick, db)
        except Exception:
            logger.exception("runtime_sync_worker tick failed")
        finally:
            db.close()
        await asyncio.sleep(interval)


def _run_tick(db) -> None:
    try:
        rss.process_ready_runtime_sync_queue_batch(db, batch_limit=8)
    except Exception:
        logger.exception("runtime_sync queue batch failed")

    rows = db.execute(
        text(
            """
            SELECT id, region
            FROM lockers
            WHERE active = TRUE
            ORDER BY id
            """
        )
    ).mappings().all()
    for row in rows:
        lid = str(row["id"])
        region = str(row.get("region") or "").strip() or None
        try:
            rss.sync_locker_slots_from_runtime(db, lid, region=region)
        except Exception:
            logger.exception("runtime sync locker failed locker_id=%s", lid)
