# 01_source/payment_gateway/app/services/postgres_capability_service.py
# 07/04/2026

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from threading import RLock
from typing import Any, Dict, List, Optional

import psycopg2
import psycopg2.extras

from app.core.config import settings


class CapabilityServiceError(RuntimeError):
    pass


@dataclass(frozen=True)
class CapabilitySnapshot:
    fetched_at: float
    lockers: Dict[str, dict]
    regions: set[str]
    channels: set[str]
    payment_methods: set[str]


class PostgresCapabilityService:
    """
    Fonte primária de capabilities/lockers via Postgres central.
    Cache em memória com TTL.
    """

    def __init__(
        self,
        dsn: Optional[str] = None,
        cache_ttl_sec: Optional[int] = None,
    ) -> None:
        self.dsn = (
            dsn
            or os.getenv("PAYMENT_GATEWAY_POSTGRES_DSN")
            or os.getenv("CENTRAL_POSTGRES_DSN")
            or ""
        ).strip()
        self.cache_ttl_sec = int(
            cache_ttl_sec
            or os.getenv("PAYMENT_GATEWAY_CAPABILITY_CACHE_TTL_SEC")
            or 10
        )
        self._lock = RLock()
        self._snapshot: Optional[CapabilitySnapshot] = None

    def is_enabled(self) -> bool:
        return bool(self.dsn)

    def _connect(self):
        if not self.dsn:
            raise CapabilityServiceError(
                "Postgres DSN não configurado em PAYMENT_GATEWAY_POSTGRES_DSN/CENTRAL_POSTGRES_DSN."
            )
        return psycopg2.connect(self.dsn, cursor_factory=psycopg2.extras.RealDictCursor)

    def _cache_valid(self) -> bool:
        if not self._snapshot:
            return False
        age = time.time() - self._snapshot.fetched_at
        return age <= self.cache_ttl_sec

    def get_snapshot(self, force_refresh: bool = False) -> CapabilitySnapshot:
        with self._lock:
            if not force_refresh and self._cache_valid():
                return self._snapshot  # type: ignore[return-value]

            snapshot = self._fetch_snapshot()
            self._snapshot = snapshot
            return snapshot

    def get_stale_snapshot(self) -> Optional[CapabilitySnapshot]:
        with self._lock:
            return self._snapshot

    def _fetch_snapshot(self) -> CapabilitySnapshot:
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT code
                        FROM public.capability_region
                        WHERE is_active = TRUE
                        """
                    )
                    regions = {
                        str(row["code"] or "").strip().upper()
                        for row in cur.fetchall()
                        if str(row["code"] or "").strip()
                    }

                    cur.execute(
                        """
                        SELECT code
                        FROM public.capability_channel
                        WHERE is_active = TRUE
                        """
                    )
                    channels = {
                        str(row["code"] or "").strip().upper()
                        for row in cur.fetchall()
                        if str(row["code"] or "").strip()
                    }

                    cur.execute(
                        """
                        SELECT code
                        FROM public.payment_method_catalog
                        WHERE is_active = TRUE
                        """
                    )
                    payment_methods = {
                        str(row["code"] or "").strip()
                        for row in cur.fetchall()
                        if str(row["code"] or "").strip()
                    }

                    # Fonte principal de lockers
                    cur.execute(
                        """
                        SELECT
                            locker_id,
                            region,
                            site_id,
                            display_name,
                            backend_region,
                            slots,
                            channels,
                            payment_methods,
                            active,
                            address_json
                        FROM public.runtime_lockers
                        WHERE active = TRUE
                        """
                    )
                    rows = cur.fetchall()

        except Exception as exc:
            raise CapabilityServiceError(
                f"Falha ao carregar capabilities/lockers do Postgres: {exc}"
            ) from exc

        lockers: Dict[str, dict] = {}
        for row in rows:
            locker_id = str(row.get("locker_id") or "").strip().upper()
            if not locker_id:
                continue

            lockers[locker_id] = {
                "locker_id": locker_id,
                "region": str(row.get("region") or "").strip().upper(),
                "site_id": row.get("site_id"),
                "display_name": row.get("display_name") or locker_id,
                "backend_region": str(
                    row.get("backend_region") or row.get("region") or ""
                ).strip().upper(),
                "slots": int(row.get("slots") or 0),
                "channels": list(row.get("channels") or []),
                "payment_methods": list(row.get("payment_methods") or []),
                "active": bool(row.get("active")),
                "address": row.get("address_json") or {},
            }

        return CapabilitySnapshot(
            fetched_at=time.time(),
            lockers=lockers,
            regions=regions,
            channels=channels,
            payment_methods=payment_methods,
        )


