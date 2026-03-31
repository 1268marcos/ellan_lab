# 01_source/payment_gateway/app/core/event_log.py

from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, Optional

from app.core.hashing import sha256_prefixed, canonical_json


def _epoch() -> int:
    return int(time.time())


def _today_ymd() -> str:
    return time.strftime("%Y-%m-%d", time.localtime())


def _ensure_dir(path: str) -> None:
    folder = os.path.dirname(path)
    if folder and not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)


class GatewayEventLogger:
    """
    Log encadeado JSONL:
      - cada linha = 1 evento
      - hash = sha256(salt + canonical_json(payload + prev_hash))
    """

    def __init__(self, *, gateway_id: str, log_dir: str, log_hash_salt: str):
        self.gateway_id = gateway_id
        self.log_dir = log_dir
        self.log_hash_salt = log_hash_salt

    def salt_fingerprint(self) -> str:
        return sha256_prefixed(self.log_hash_salt)

    def _path_for_day(self, ymd: str) -> str:
        return os.path.join(self.log_dir, f"gateway_events_{ymd}.jsonl")

    def _read_last_hash(self, path: str) -> Optional[str]:
        if not os.path.exists(path):
            return None
        try:
            with open(path, "rb") as f:
                f.seek(0, os.SEEK_END)
                size = f.tell()
                if size == 0:
                    return None
                # lê o final do arquivo procurando a última linha
                offset = min(4096, size)
                f.seek(-offset, os.SEEK_END)
                tail = f.read().decode("utf-8", errors="ignore")
            lines = [ln for ln in tail.splitlines() if ln.strip()]
            if not lines:
                return None
            obj = json.loads(lines[-1])
            return obj.get("hash")
        except Exception:
            return None

    def append_event(self, *, event: Dict[str, Any], ymd: Optional[str] = None) -> Dict[str, Any]:
        ymd = ymd or _today_ymd()
        path = self._path_for_day(ymd)
        _ensure_dir(path)

        prev_hash = self._read_last_hash(path)

        payload = {
            "gateway_id": self.gateway_id,
            "ts": _epoch(),
            "event": event,
            "prev_hash": prev_hash,
        }

        computed = sha256_prefixed(self.log_hash_salt + "::" + canonical_json(payload))

        line = {
            **payload,
            "hash": computed,
            "salt_fingerprint": self.salt_fingerprint(),
        }

        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(line, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n")

        return {
            "ok": True,
            "ymd": ymd,
            "path": path,
            "prev_hash": prev_hash,
            "hash": computed,
            "salt_fingerprint": line["salt_fingerprint"],
        }

    def verify_chain(self, ymd: str) -> Dict[str, Any]:
        path = self._path_for_day(ymd)
        if not os.path.exists(path):
            return {
                "ok": True,
                "status": "missing_file",
                "message": "Arquivo não existe (sem eventos no dia).",
                "ymd": ymd,
                "path": path,
                "checked": 0,
            }

        prev = None
        checked = 0
        last_hash = None

        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    obj = json.loads(line)

                    stored_hash = obj.get("hash")
                    stored_prev = obj.get("prev_hash")

                    core = dict(obj)
                    core.pop("hash", None)
                    core.pop("salt_fingerprint", None)

                    computed = sha256_prefixed(self.log_hash_salt + "::" + canonical_json(core))

                    if stored_prev != prev:
                        return {
                            "ok": False,
                            "status": "prev_hash_mismatch",
                            "checked": checked,
                            "expected_prev": prev,
                            "found_prev": stored_prev,
                            "path": path,
                        }

                    if computed != stored_hash:
                        return {
                            "ok": False,
                            "status": "hash_mismatch",
                            "checked": checked,
                            "computed_hash": computed,
                            "stored_hash": stored_hash,
                            "path": path,
                        }

                    prev = stored_hash
                    last_hash = stored_hash
                    checked += 1

            return {
                "ok": True,
                "status": "verified",
                "checked": checked,
                "last_hash": last_hash,
                "path": path,
            }
        except Exception as e:
            return {
                "ok": False,
                "status": "verify_exception",
                "checked": checked,
                "path": path,
                "error": str(e),
            }