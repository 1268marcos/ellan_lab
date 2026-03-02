import os
import json
from pathlib import Path
from typing import Any, Dict, Optional

from app.core.event_log import _sha256


def verify_snapshot_file(
    *,
    machine_id: str,
    date_utc: str,
    base_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Verifica integridade do snapshot antifraude salvo em disco.

    - Lê: 05_backups/daily/antifraud/{machine_id}_{date_utc}.json
    - Recalcula snapshot_hash usando LOG_HASH_SALT
    - Compara com snapshot_hash do arquivo
    """
    salt = os.getenv("LOG_HASH_SALT", "")
    if not salt:
        return {"ok": False, "reason": "LOG_HASH_SALT_not_set"}

    home = str(Path.home())
    root = base_dir or f"{home}/ellan_lab"

    path = Path(root) / "05_backups" / "daily" / "antifraud" / f"{machine_id}_{date_utc}.json"
    if not path.exists():
        return {"ok": False, "reason": "file_not_found", "path": str(path)}

    raw = path.read_text(encoding="utf-8")
    try:
        data = json.loads(raw)
    except Exception as e:
        return {"ok": False, "reason": "invalid_json", "path": str(path), "detail": str(e)}

    file_hash = data.get("snapshot_hash")
    if not file_hash:
        return {"ok": False, "reason": "snapshot_hash_missing", "path": str(path)}

    # remove snapshot_hash para recalcular exatamente o que foi assinado
    data_copy = dict(data)
    data_copy.pop("snapshot_hash", None)

    payload_json = json.dumps(data_copy, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    expected = _sha256(payload_json + "|" + salt)

    return {
        "ok": expected == file_hash,
        "machine_id": machine_id,
        "date_utc": date_utc,
        "path": str(path),
        "snapshot_hash_file": file_hash,
        "snapshot_hash_expected": expected,
        "tampered": expected != file_hash,
    }