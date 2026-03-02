import time
from typing import Any, Dict

from app.services.sqlite_service import SQLiteService


class DeviceRegistryService:
    def __init__(self, sqlite: SQLiteService):
        self.sqlite = sqlite

    def _now(self) -> int:
        return int(time.time())

    def touch(self, device_hash: str, version: str) -> Dict[str, Any]:
        """
        Upsert simples.
        Retorna:
          - known: bool
          - seen_count: int
          - first_seen_at, last_seen_at
        """
        now = self._now()

        with self.sqlite.session() as conn:
            row = conn.execute(
                "SELECT device_hash, first_seen_at, last_seen_at, seen_count FROM device_registry WHERE device_hash = ?",
                (device_hash,),
            ).fetchone()

            if not row:
                conn.execute(
                    """
                    INSERT INTO device_registry (device_hash, version, first_seen_at, last_seen_at, seen_count, flags_json)
                    VALUES (?, ?, ?, ?, 1, '{}')
                    """,
                    (device_hash, version, now, now),
                )
                return {"known": False, "seen_count": 1, "first_seen_at": now, "last_seen_at": now}

            seen_count = int(row["seen_count"]) + 1
            first_seen_at = int(row["first_seen_at"])

            conn.execute(
                """
                UPDATE device_registry
                SET last_seen_at = ?, seen_count = ?
                WHERE device_hash = ?
                """,
                (now, seen_count, device_hash),
            )

            return {"known": True, "seen_count": seen_count, "first_seen_at": first_seen_at, "last_seen_at": now}