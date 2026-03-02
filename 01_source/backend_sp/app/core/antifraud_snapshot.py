import os
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

from app.core.db import get_conn
from app.core.event_log import _sha256


def _utc_date_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def get_last_event_info(machine_id: str):
    conn = get_conn()

    cur_count = conn.execute(
        "SELECT COUNT(1) FROM events WHERE machine_id = ?;",
        (machine_id,),
    )
    events_count = cur_count.fetchone()[0]

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
        "events_count": int(events_count),
        "last_event_id": int(row[0]),
        "last_event_ts": row[1],
        "last_hash": row[2],
    }


def _read_snapshot_hash(path: Path) -> str | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("snapshot_hash")
    except Exception:
        return None


def _find_previous_snapshot_hash(backup_dir: Path, machine_id: str, date_utc: str) -> str | None:
    """
    Procura o snapshot do dia anterior.
    """
    try:
        d = datetime.strptime(date_utc, "%Y-%m-%d")
    except Exception:
        return None

    prev_date = (d - timedelta(days=1)).strftime("%Y-%m-%d")
    prev_path = backup_dir / f"{machine_id}_{prev_date}.json"
    if not prev_path.exists():
        return None

    return _read_snapshot_hash(prev_path)


def create_daily_snapshot(machine_id: str, base_dir: str | None = None):
    """
    Snapshot diário antifraude (com encadeamento):
    - assina snapshot com LOG_HASH_SALT
    - inclui previous_snapshot_hash (dia anterior)
    - grava em:
      - 05_backups/daily/antifraud/
      - 04_logs/antifraud/
    """
    salt = os.getenv("LOG_HASH_SALT", "")
    if not salt:
        raise RuntimeError("LOG_HASH_SALT is not set. Snapshot requires it.")

    events_db_path = os.getenv("EVENTS_DB_PATH")
    salt_fingerprint = _sha256(salt)

    config_payload = json.dumps(
    {
        "machine_id": machine_id,
        "events_db_path": events_db_path,
        "salt_fingerprint": salt_fingerprint,
    },
    sort_keys=True,
    separators=(",", ":"),
    )

    config_fingerprint = _sha256(config_payload)

    info = get_last_event_info(machine_id)
    date = _utc_date_str()

    # Paths (precisa vir ANTES para buscar snapshot anterior)
    home = str(Path.home())
    default_base = base_dir or f"{home}/ellan_lab"

    backup_dir = Path(default_base) / "05_backups" / "daily" / "antifraud"
    backup_dir.mkdir(parents=True, exist_ok=True)

    logs_dir = Path(default_base) / "04_logs" / "antifraud"
    logs_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{machine_id}_{date}.json"
    backup_path = backup_dir / filename
    logs_path = logs_dir / filename

    # Encadeamento: pega hash do snapshot anterior (se existir)
    previous_snapshot_hash = _find_previous_snapshot_hash(backup_dir, machine_id, date)

    # Monta snapshot (SEM snapshot_hash)
    snapshot = {
        "machine_id": machine_id,
        "date_utc": date,
        "events_count": info["events_count"],
        "last_event_id": info["last_event_id"],
        "last_event_ts": info["last_event_ts"],
        "last_hash": info["last_hash"],
        "previous_snapshot_hash": previous_snapshot_hash,

        # 🔐 Auditoria de ambiente
        "events_db_path": events_db_path,
        "salt_fingerprint": salt_fingerprint,
        "config_fingerprint": config_fingerprint,

        "verify_endpoint": f"/audit/verify?machine_id={machine_id}",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "version": 4,  # incrementa versão por causa do encadeamento
    }

    # Assina o snapshot (hash do JSON + salt)
    payload_json = json.dumps(snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    snapshot_hash = _sha256(payload_json + "|" + salt)
    snapshot["snapshot_hash"] = snapshot_hash

    # Grava JSON final
    final_json = json.dumps(snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
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
        "version": 2,
    }