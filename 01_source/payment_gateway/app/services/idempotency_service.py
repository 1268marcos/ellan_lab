import json
import time
import uuid
from typing import Any, Dict, Optional, Tuple

from app.services.sqlite_service import SQLiteService


class IdempotencyService:
    def __init__(self, sqlite: SQLiteService, ttl_sec: int):
        self.sqlite = sqlite
        self.ttl_sec = ttl_sec

    def _now(self) -> int:
        return int(time.time())

    def cleanup_expired(self) -> None:
        now = self._now()
        with self.sqlite.session() as conn:
            conn.execute("DELETE FROM idempotency_keys WHERE expires_at < ?", (now,))

    def check(self, endpoint: str, idem_key: str, payload_hash: str) -> Dict[str, Any]:
        """
        Retorna:
          - hit: bool
          - status: "new" | "replayed" | "payload_mismatch"
          - stored_response: dict | None
          - original_payload_hash: str | None
        """
        self.cleanup_expired()

        with self.sqlite.session() as conn:
            row = conn.execute(
                """
                SELECT payload_hash, response_blob
                FROM idempotency_keys
                WHERE endpoint = ? AND idem_key = ?
                """,
                (endpoint, idem_key),
            ).fetchone()

        if not row:
            return {"hit": False, "status": "new", "stored_response": None, "original_payload_hash": None}

        original_hash = row["payload_hash"]
        if original_hash == payload_hash:
            return {
                "hit": True,
                "status": "replayed",
                "stored_response": json.loads(row["response_blob"]),
                "original_payload_hash": original_hash,
            }

        return {
            "hit": True,
            "status": "payload_mismatch",
            "stored_response": None,
            "original_payload_hash": original_hash,
        }

   
    def store(
        self,
        endpoint: str,
        idem_key: str,
        payload_hash: str,
        response_obj: Dict[str, Any],
        status: str = "stored",
    ) -> Dict[str, Any]:
        """
        Store idempotency record.
        Se já existir (UNIQUE endpoint+idem_key), não dá erro:
        - se payload_hash bater -> retorna "replayed" e response armazenada
        - se payload_hash divergir -> retorna "payload_mismatch" e original_payload_hash
        """
        now = self._now()
        expires_at = now + int(self.ttl_sec)

        record_id = f"idem_{uuid.uuid4().hex}"
        response_blob = json.dumps(response_obj, ensure_ascii=False, separators=(",", ":"), sort_keys=True)

        with self.sqlite.session() as conn:
            # 1) Tenta inserir. Se já existir, IGNORE (não explode).
            cur = conn.execute(
                """
                INSERT OR IGNORE INTO idempotency_keys
                (id, endpoint, idem_key, payload_hash, response_blob, status, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (record_id, endpoint, idem_key, payload_hash, response_blob, status, now, expires_at),
            )

            # 2) Se inseriu de fato, pronto.
            if cur.rowcount == 1:
                return {
                    "status": "stored",
                    "stored_response": response_obj,
                    "original_payload_hash": payload_hash,
                }

            # 3) Se não inseriu (IGNORED), busca o registro existente e decide.
            row = conn.execute(
                """
                SELECT payload_hash, response_blob
                FROM idempotency_keys
                WHERE endpoint = ? AND idem_key = ?
                """,
                (endpoint, idem_key),
            ).fetchone()

            if not row:
                # Caso raríssimo: IGNORE mas não achou (concorrência bizarra). Trate como stored.
                return {
                    "status": "stored",
                    "stored_response": response_obj,
                    "original_payload_hash": payload_hash,
                }

            original_hash = row["payload_hash"]

            if original_hash == payload_hash:
                return {
                    "status": "replayed",
                    "stored_response": json.loads(row["response_blob"]),
                    "original_payload_hash": original_hash,
                }

            return {
                "status": "payload_mismatch",
                "stored_response": None,
                "original_payload_hash": original_hash,
            }