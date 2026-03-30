# 01_source/backend/runtime/app/core/antifraud_snapshot_verify.py
import os
import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from app.core.db import get_conn


def _sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _sha256_prefixed(s: str) -> str:
    return "sha256:" + _sha256_hex(s)


def _canonical_json(obj: dict) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _resolve_backups_base(base_dir: Optional[str]) -> Path:
    """
    Prioridade:
    1) base_dir param -> <base_dir>/05_backups
    2) env BACKUPS_DIR
    3) /backups (docker)
    4) ~/ellan_lab/05_backups (local)
    """
    if base_dir:
        return Path(base_dir) / "05_backups"

    backups_env = os.getenv("BACKUPS_DIR")
    if backups_env:
        return Path(backups_env)

    if Path("/backups").exists():
        return Path("/backups")

    return Path.home() / "ellan_lab" / "05_backups"


def _read_json(path: Path) -> tuple[dict | None, str | None]:
    try:
        raw = path.read_text(encoding="utf-8")
        return json.loads(raw), None
    except Exception as e:
        return None, str(e)


def _get_snapshot_path(backups_base: Path, machine_id: str, date_utc: str) -> Path:
    return backups_base / "daily" / "antifraud" / f"{machine_id}_{date_utc}.json"


def _prev_date(date_utc: str) -> str | None:
    try:
        d = datetime.strptime(date_utc, "%Y-%m-%d")
        return (d - timedelta(days=1)).strftime("%Y-%m-%d")
    except Exception:
        return None


def _day_end_iso(date_utc: str) -> str | None:
    try:
        d = datetime.strptime(date_utc, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        end = d.replace(hour=23, minute=59, second=59, microsecond=999999)
        return end.isoformat()
    except Exception:
        return None

def _get_last_event_hash(machine_id: str, date_utc: str) -> str | None:
    end_iso = _day_end_iso(date_utc)
    if not end_iso:
        return None
    conn = get_conn()
    cur = conn.execute(
        """
        SELECT hash
        FROM events
        WHERE machine_id=? AND ts <= ?
        ORDER BY id DESC
        LIMIT 1;
        """,
        (machine_id, end_iso),
    )
    row = cur.fetchone()
    return row[0] if row else None


def verify_snapshot_file(
    *,
    machine_id: str,
    date_utc: str,
    base_dir: Optional[str] = None,
    verify_previous: bool = True,
    verify_against_events_db: bool = True,
) -> Dict[str, Any]:
    """
    Verifica integridade do snapshot antifraude salvo em disco.

    - Lê: <backups>/daily/antifraud/{machine_id}_{date_utc}.json
    - Recalcula snapshot_hash usando LOG_HASH_SALT
    - Compara com snapshot_hash do arquivo
    - (opcional) valida previous_snapshot_hash (cadeia diária)
    - (opcional) valida last_hash vs último evento do events.db
    """
    salt = os.getenv("LOG_HASH_SALT", "")
    if not salt:
        return {
            "ok": False,
            "reason": "LOG_HASH_SALT_not_set",
            "retryable": False,
            "machine_id": machine_id,
            "date_utc": date_utc,
        }

    backups_base = _resolve_backups_base(base_dir)
    path = _get_snapshot_path(backups_base, machine_id, date_utc)

    if not path.exists():
        return {
            "ok": False,
            "reason": "file_not_found",
            "retryable": True,
            "machine_id": machine_id,
            "date_utc": date_utc,
            "path": str(path),
        }

    data, err = _read_json(path)
    if err or not isinstance(data, dict):
        return {
            "ok": False,
            "reason": "invalid_json",
            "retryable": False,
            "machine_id": machine_id,
            "date_utc": date_utc,
            "path": str(path),
            "detail": err,
        }

    file_hash = data.get("snapshot_hash")
    if not file_hash:
        return {
            "ok": False,
            "reason": "snapshot_hash_missing",
            "retryable": False,
            "machine_id": machine_id,
            "date_utc": date_utc,
            "path": str(path),
        }

    # remove snapshot_hash para recalcular exatamente o que foi assinado
    data_copy = dict(data)
    data_copy.pop("snapshot_hash", None)

    payload_json = _canonical_json(data_copy)
    expected = _sha256_prefixed(payload_json + "|" + salt)

    tampered = expected != file_hash

    # --------- validação do snapshot anterior (cadeia diária) ----------
    prev_check = None
    if verify_previous:
        prev_hash_declared = data.get("previous_snapshot_hash")
        prev_date = _prev_date(date_utc)

        if prev_hash_declared and prev_date:
            prev_path = _get_snapshot_path(backups_base, machine_id, prev_date)
            if not prev_path.exists():
                prev_check = {
                    "ok": False,
                    "reason": "previous_snapshot_missing",
                    "prev_date_utc": prev_date,
                    "prev_path": str(prev_path),
                    "declared_previous_snapshot_hash": prev_hash_declared,
                }
            else:
                prev_data, prev_err = _read_json(prev_path)
                if prev_err or not isinstance(prev_data, dict):
                    prev_check = {
                        "ok": False,
                        "reason": "previous_snapshot_invalid_json",
                        "prev_date_utc": prev_date,
                        "prev_path": str(prev_path),
                        "detail": prev_err,
                    }
                else:
                    prev_file_hash = prev_data.get("snapshot_hash")
                    prev_check = {
                        "ok": (prev_file_hash == prev_hash_declared),
                        "prev_date_utc": prev_date,
                        "prev_path": str(prev_path),
                        "declared_previous_snapshot_hash": prev_hash_declared,
                        "previous_snapshot_hash_file": prev_file_hash,
                        "tampered": (prev_file_hash != prev_hash_declared),
                    }
        else:
            # sem previous hash declarado (primeiro dia) — ok
            prev_check = {"ok": True, "reason": "no_previous_snapshot_hash_declared"}

    # --------- validação contra events.db ----------
    events_db_check = None
    if verify_against_events_db:
        snapshot_last_hash = data.get("last_hash")
        current_last_hash = _get_last_event_hash(machine_id, date_utc)

        # Se não há eventos, ambos podem ser None; isso é ok.
        events_db_check = {
            "ok": (snapshot_last_hash == current_last_hash),
            "snapshot_last_hash": snapshot_last_hash,
            "events_db_last_hash": current_last_hash,
            "tampered_or_drift": (snapshot_last_hash != current_last_hash),
        }

    ok = (not tampered)
    if verify_previous and prev_check and prev_check.get("ok") is False:
        ok = False
    if verify_against_events_db and events_db_check and events_db_check.get("ok") is False:
        ok = False

    return {
        "ok": ok,
        "machine_id": machine_id,
        "date_utc": date_utc,
        "path": str(path),
        "snapshot_hash_file": file_hash,
        "snapshot_hash_expected": expected,
        "tampered": tampered,
        "previous_snapshot_check": prev_check,
        "events_db_check": events_db_check,
    }