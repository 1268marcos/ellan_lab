# 01_source/payment_gateway/app/core/antifraud_snapshot.py

from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List, Optional

from app.core.hashing import canonical_json, sha256_prefixed
from app.services.sqlite_service import SQLiteService
from app.services.risk_events_service import RiskEventsService
from app.core.event_log import GatewayEventLogger


def _epoch_now() -> int:
    return int(time.time())


def _today_ymd() -> str:
    return time.strftime("%Y-%m-%d", time.localtime())

def _ymd_to_day_range_epoch(ymd: str) -> tuple[int, int]:
    """
    Converte YYYY-MM-DD para intervalo local do dia:
    00:00:00 até 23:59:59 (inclusive).
    """
    t0 = time.strptime(ymd + " 00:00:00", "%Y-%m-%d %H:%M:%S")
    start = int(time.mktime(t0))
    end = start + 86399
    return start, end

def _ensure_dir(path: str) -> None:
    folder = os.path.dirname(path)
    if folder and not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)


def _write_json(path: str, obj: Dict[str, Any]) -> None:
    _ensure_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)


def _read_json(path: str) -> Optional[Dict[str, Any]]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def _top_reasons_from_stats(stats: Dict[str, Any]) -> List[Dict[str, Any]]:
    # stats já tem top_reasons, só normaliza
    tr = stats.get("top_reasons") or []
    out = []
    for item in tr[:10]:
        out.append({"code": item.get("code", "UNKNOWN"), "count": int(item.get("count", 0))})
    return out


class GatewaySnapshotService:
    def __init__(
        self,
        *,
        sqlite: SQLiteService,
        logger: GatewayEventLogger,
        snapshots_dir: str,
        backups_dir: str,
        pepper_fingerprint: str,
        config_fingerprint: str,
    ):
        self.sqlite = sqlite
        self.logger = logger
        self.snapshots_dir = snapshots_dir
        self.backups_dir = backups_dir
        self.pepper_fingerprint = pepper_fingerprint
        self.config_fingerprint = config_fingerprint

    def snapshot_paths(self, ymd: str) -> Dict[str, str]:
        return {
            "snapshot_path": os.path.join(self.snapshots_dir, f"GATEWAY_{ymd}.json"),
            "backup_path": os.path.join(self.backups_dir, f"GATEWAY_{ymd}.json"),
        }

    def _ymd_to_day_range_epoch(ymd: str) -> tuple[int, int]:
        """
        Converte YYYY-MM-DD para intervalo local do dia:
        00:00:00 até 23:59:59 (inclusive).
        """
        t0 = time.strptime(ymd + " 00:00:00", "%Y-%m-%d %H:%M:%S")
        start = int(time.mktime(t0))
        end = start + 86399
        return start, end

    def build_snapshot(self, ymd: str) -> Dict[str, Any]:
        """
        Snapshot do dia:
          - stats por decisão (ALLOW/CHALLENGE/BLOCK)
          - top reasons
          - last_hash do log encadeado do dia (anchor)
          - fingerprints (pepper/config/salt)
        """

        self.sqlite.migrate()
        svc = RiskEventsService(self.sqlite)

        start_epoch, end_epoch = _ymd_to_day_range_epoch(ymd)
        fx = svc.forensics_between(start_epoch, end_epoch)

        log_verify = self.logger.verify_chain(ymd)

        snapshot_core = {
            "service": "payment_gateway",
            "snapshot_type": "GATEWAY_DAILY",
            "date": ymd,
            "created_at": _epoch_now(),

            # Contrato "forense" - dá pra bater o olho e entender o dia, e ainda tem amostras pra investigação.
            # ✅ auditoria por faixa do dia
            "stats": {
                "window": fx["window"],
                "totals": {"events": fx["integrity"]["total_events"]},
                "decisions": fx["stats"]["decisions"],
                "top_reasons": fx["stats"]["top_reasons"],
            },

            # ✅ forense
            "events_sample": fx["events_sample"],
            "policy_ids_used": fx["policy_ids_used"],
            "integrity": fx["integrity"],

            # ✅ ancora no log encadeado do dia
            "log_anchor": {
                "log_date": ymd,
                "log_path": log_verify.get("path"),
                "log_ok": log_verify.get("ok"),
                "checked": log_verify.get("checked", 0),
                "last_hash": log_verify.get("last_hash"),
                "status": log_verify.get("status"),
            },

            "fingerprints": {
                "pepper_fingerprint": self.pepper_fingerprint,
                "config_fingerprint": self.config_fingerprint,
                "salt_fingerprint": self.logger.salt_fingerprint(),
            },
        }

        # hash do snapshot (impressão digital)
        snapshot_hash = sha256_prefixed(canonical_json(snapshot_core))

        snapshot = {
            **snapshot_core,
            "snapshot_hash": snapshot_hash,
        }

        return snapshot

    def write_snapshot(self, ymd: Optional[str] = None) -> Dict[str, Any]:
        ymd = ymd or _today_ymd()
        snap = self.build_snapshot(ymd)
        paths = self.snapshot_paths(ymd)

        _write_json(paths["snapshot_path"], snap)
        _write_json(paths["backup_path"], snap)

        return {
            "ok": True,
            "date": ymd,
            "snapshot_path": paths["snapshot_path"],
            "backup_path": paths["backup_path"],
            "snapshot_hash": snap["snapshot_hash"],
        }

    def read_snapshot(self, ymd: str) -> Optional[Dict[str, Any]]:
        paths = self.snapshot_paths(ymd)
        return _read_json(paths["snapshot_path"])