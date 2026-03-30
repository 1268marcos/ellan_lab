# 01_source/backend/runtime/app/core/antifraud_snapshot.py
import os
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Optional

from app.core.db import get_conn

SNAPSHOT_VERSION = 7  # bump: snapshot histórico real (as-of date)

def _validate_date_utc(date_utc: str) -> str:
    try:
        datetime.strptime(date_utc, "%Y-%m-%d")
    except Exception:
        raise ValueError("date_utc must be in YYYY-MM-DD (UTC)")
    return date_utc

def _utc_date_str_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")

def _day_bounds_utc_iso(date_utc: str) -> tuple[str, str]:
    """
    Retorna start/end ISO UTC com offset +00:00.
    Usamos end inclusive com microsegundos.
    """
    d = datetime.strptime(date_utc, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    start = d.replace(hour=0, minute=0, second=0, microsecond=0)
    end = d.replace(hour=23, minute=59, second=59, microsecond=999999)
    return (start.isoformat(), end.isoformat())

def _sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def _sha256_prefixed(s: str) -> str:
    return "sha256:" + _sha256_hex(s)

def _canonical_json(obj: dict) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def _read_snapshot_hash(path: Path) -> str | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("snapshot_hash")
    except Exception:
        return None

def _find_previous_snapshot_hash(backup_dir: Path, machine_id: str, date_utc: str) -> str | None:
    try:
        d = datetime.strptime(date_utc, "%Y-%m-%d")
    except Exception:
        return None
    prev_date = (d - timedelta(days=1)).strftime("%Y-%m-%d")
    prev_path = backup_dir / f"{machine_id}_{prev_date}.json"
    if not prev_path.exists():
        return None
    return _read_snapshot_hash(prev_path)

def _resolve_base_dirs(base_dir: str | None):
    """
    Prioridade:
    1) base_dir param
    2) env BACKUPS_DIR / LOGS_DIR
    3) /backups e /logs
    4) ~/ellan_lab/05_backups e ~/ellan_lab/04_logs
    """
    if base_dir:
        base = Path(base_dir)
        return (base / "05_backups", base / "04_logs")

    backups_env = os.getenv("BACKUPS_DIR")
    logs_env = os.getenv("LOGS_DIR")
    if backups_env and logs_env:
        return (Path(backups_env), Path(logs_env))

    if Path("/backups").exists() and Path("/logs").exists():
        return (Path("/backups"), Path("/logs"))

    home = Path.home()
    return (home / "ellan_lab" / "05_backups", home / "ellan_lab" / "04_logs")

def get_last_event_info(machine_id: str, *, date_utc: Optional[str] = None) -> dict:
    """
    Se date_utc for fornecido, retorna métricas históricas:
    - count de eventos até o fim do dia UTC
    - último evento (id, ts, hash) até o fim do dia UTC
    """
    conn = get_conn()

    if date_utc:
        date_utc = _validate_date_utc(date_utc)
        _start_iso, end_iso = _day_bounds_utc_iso(date_utc)

        cur_count = conn.execute(
            "SELECT COUNT(1) FROM events WHERE machine_id=? AND ts <= ?;",
            (machine_id, end_iso),
        )
        events_count = int(cur_count.fetchone()[0])

        cur_last = conn.execute(
            """
            SELECT id, ts, hash
            FROM events
            WHERE machine_id=? AND ts <= ?
            ORDER BY id DESC
            LIMIT 1;
            """,
            (machine_id, end_iso),
        )
        row = cur_last.fetchone()

        if row is None:
            return {
                "events_count": 0,
                "last_event_id": None,
                "last_event_ts": None,
                "last_hash": None,
                "as_of_date_utc": date_utc,
                "as_of_end_iso": end_iso,
            }

        return {
            "events_count": events_count,
            "last_event_id": int(row[0]),
            "last_event_ts": row[1],
            "last_hash": row[2],
            "as_of_date_utc": date_utc,
            "as_of_end_iso": end_iso,
        }

    # fallback: “agora” (comportamento antigo)
    cur_count = conn.execute(
        "SELECT COUNT(1) FROM events WHERE machine_id = ?;",
        (machine_id,),
    )
    events_count = int(cur_count.fetchone()[0])

    cur_last = conn.execute(
        "SELECT id, ts, hash FROM events WHERE machine_id = ? ORDER BY id DESC LIMIT 1;",
        (machine_id,),
    )
    row = cur_last.fetchone()

    if row is None:
        return {
            "events_count": 0,
            "last_event_id": None,
            "last_event_ts": None,
            "last_hash": None,
        }

    return {
        "events_count": events_count,
        "last_event_id": int(row[0]),
        "last_event_ts": row[1],
        "last_hash": row[2],
    }

def create_daily_snapshot(*, machine_id: str, base_dir: str | None = None, date_utc: Optional[str] = None):
    """
    Snapshot diário antifraude (histórico real se date_utc for dado):
    - last_hash/last_event_id/events_count refletem o DB até o fim daquele dia UTC
    - assinatura com LOG_HASH_SALT
    - encadeamento com previous_snapshot_hash (dia anterior)
    """
    salt = os.getenv("LOG_HASH_SALT", "")
    if not salt:
        raise RuntimeError("LOG_HASH_SALT is not set. Snapshot requires it.")

    date = _validate_date_utc(date_utc) if date_utc else _utc_date_str_now()

    events_db_path = os.getenv("EVENTS_DB_PATH") or os.getenv("DATABASE_URL") or None
    salt_fingerprint = _sha256_prefixed(salt)

    config_payload = _canonical_json({
        "machine_id": machine_id,
        "events_db_path": events_db_path,
        "salt_fingerprint": salt_fingerprint,
    })
    config_fingerprint = _sha256_prefixed(config_payload)

    # ✅ histórico real “as of date”
    info = get_last_event_info(machine_id, date_utc=date)

    backups_base, logs_base = _resolve_base_dirs(base_dir)

    backup_dir = backups_base / "daily" / "antifraud"
    backup_dir.mkdir(parents=True, exist_ok=True)

    logs_dir = logs_base / "antifraud"
    logs_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{machine_id}_{date}.json"
    backup_path = backup_dir / filename
    logs_path = logs_dir / filename

    previous_snapshot_hash = _find_previous_snapshot_hash(backup_dir, machine_id, date)

    snapshot = {
        "machine_id": machine_id,
        "date_utc": date,

        # ✅ histórico real
        "events_count": info["events_count"],
        "last_event_id": info["last_event_id"],
        "last_event_ts": info["last_event_ts"],
        "last_hash": info["last_hash"],
        "as_of_end_iso": info.get("as_of_end_iso"),

        "previous_snapshot_hash": previous_snapshot_hash,

        # auditoria de ambiente
        "events_db_path": events_db_path,
        "salt_fingerprint": salt_fingerprint,
        "config_fingerprint": config_fingerprint,

        "verify_endpoint": f"/audit/snapshot/verify_file?machine_id={machine_id}&date_utc={date}",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "version": SNAPSHOT_VERSION,
    }

    payload_json = _canonical_json(snapshot)
    snapshot_hash = _sha256_prefixed(payload_json + "|" + salt)
    snapshot["snapshot_hash"] = snapshot_hash

    final_json = _canonical_json(snapshot)
    backup_path.write_text(final_json, encoding="utf-8")
    logs_path.write_text(final_json, encoding="utf-8")

    return {
        "ok": True,
        "machine_id": machine_id,
        "date_utc": date,
        "backup_path": str(backup_path),
        "logs_path": str(logs_path),
        "snapshot_hash": snapshot_hash,
        "previous_snapshot_hash": previous_snapshot_hash,
        "events_count": info["events_count"],
        "last_hash": info["last_hash"],
        "last_event_id": info["last_event_id"],
        "as_of_end_iso": info.get("as_of_end_iso"),
        "version": SNAPSHOT_VERSION,
    }