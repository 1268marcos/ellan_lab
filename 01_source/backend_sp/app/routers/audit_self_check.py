# 01_source/backend_sp/app/routers/audit_self_check.p
import os
import json
import hashlib
from datetime import datetime, timezone
from fastapi import APIRouter, Query, Request, Header, HTTPException

from app.core.db import get_conn
from app.core.antifraud_snapshot_verify import verify_snapshot_file

router = APIRouter(prefix="/audit", tags=["audit"])

INTERNAL_TOKEN = os.getenv("INTERNAL_TOKEN")  # opcional
DEFAULT_MACHINE_ID = os.getenv("MACHINE_ID", "CACIFO-XX-001")
REGION = os.getenv("REGION", "XX").upper()


def _require_internal_token(x_internal_token: str | None):
    if INTERNAL_TOKEN and x_internal_token != INTERNAL_TOKEN:
        raise HTTPException(
            status_code=401,
            detail={"type": "UNAUTHORIZED", "message": "invalid internal token", "retryable": False},
        )


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _utc_date_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _sha256_prefixed(s: str) -> str:
    return "sha256:" + _sha256_hex(s)


def _normalize_hash(h: str | None) -> str | None:
    if h is None:
        return None
    h = str(h)
    if h.startswith("sha256:"):
        return h
    if len(h) == 64:
        return "sha256:" + h
    return h


def _canonical_json(obj: dict) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _get_events_db_path() -> str | None:
    env_path = os.getenv("EVENTS_DB_PATH")
    if env_path:
        return env_path

    try:
        conn = get_conn()
        row = conn.execute("PRAGMA database_list;").fetchone()
        if row and len(row) >= 3:
            return row[2]
    except Exception:
        pass

    return None


def _salt_fingerprint() -> str | None:
    salt = os.getenv("LOG_HASH_SALT", "")
    if not salt:
        return None
    return _sha256_prefixed(salt)


def _config_fingerprint_current(machine_id: str) -> dict:
    salt = os.getenv("LOG_HASH_SALT", "")
    events_db_path = _get_events_db_path()

    salt_fp = _sha256_prefixed(salt) if salt else None

    payload = _canonical_json(
        {
            "machine_id": machine_id,
            "events_db_path": events_db_path,
            "salt_fingerprint": salt_fp,
        }
    )
    cfg_fp = _sha256_prefixed(payload)

    return {
        "machine_id": machine_id,
        "events_db_path": events_db_path,
        "salt_fingerprint": salt_fp,
        "config_fingerprint": cfg_fp,
    }


def _read_snapshot_config_fingerprint(machine_id: str, date_utc: str) -> dict:
    """
    Lê o config_fingerprint diretamente do arquivo de snapshot via BACKUPS_DIR (ou /backups).
    Evita hardcode de ~/ellan_lab.
    """
    # Reaproveita o resolvedor do verify_snapshot_file: chamamos ele com verify_previous=False para obter path.
    probe = verify_snapshot_file(
        machine_id=machine_id,
        date_utc=date_utc,
        verify_previous=False,
        verify_against_events_db=False,
    )
    path = probe.get("path")
    if not path:
        return {"ok": False, "reason": "snapshot_path_unknown"}

    if probe.get("reason") == "file_not_found":
        return {"ok": False, "reason": "snapshot_file_not_found", "path": path}

    try:
        raw = open(path, "r", encoding="utf-8").read()
        data = json.loads(raw)
    except Exception as e:
        return {"ok": False, "reason": "snapshot_invalid_json", "path": path, "detail": str(e)}

    cfg = data.get("config_fingerprint")
    if not cfg:
        return {"ok": False, "reason": "snapshot_config_fingerprint_missing", "path": path}

    return {"ok": True, "path": path, "config_fingerprint": cfg}


def _events_stats(machine_id: str) -> dict:
    conn = get_conn()

    total = conn.execute(
        "SELECT COUNT(1) FROM events WHERE machine_id = ?;",
        (machine_id,),
    ).fetchone()[0]

    first = conn.execute(
        "SELECT id, ts, hash FROM events WHERE machine_id = ? ORDER BY id ASC LIMIT 1;",
        (machine_id,),
    ).fetchone()

    last = conn.execute(
        "SELECT id, ts, hash FROM events WHERE machine_id = ? ORDER BY id DESC LIMIT 1;",
        (machine_id,),
    ).fetchone()

    return {
        "events_total": int(total),
        "first_event": {"id": first[0], "ts": first[1], "hash": _normalize_hash(first[2])} if first else None,
        "last_event": {"id": last[0], "ts": last[1], "hash": _normalize_hash(last[2])} if last else None,
        "bootstrap": (int(total) == 0),
    }


def _verify_event_chain(machine_id: str, max_events: int, strict_salt: bool = True) -> dict:
    """
    Verificador interno do event log (similar ao /audit/verify),
    compatível com hashes 'sha256:<hex>' e legacy.
    """
    conn = get_conn()
    salt = os.getenv("LOG_HASH_SALT", "")

    if strict_salt and not salt:
        return {
            "ok": False,
            "reason": "salt_not_set",
            "detail": "LOG_HASH_SALT is not set (strict mode)",
            "events_checked": 0,
            "max_events": max_events,
        }

    cur = conn.execute(
        """
        SELECT id, ts, machine_id, door_id, event_type, severity, correlation_id,
               sale_id, command_id, old_state, new_state, payload_json, prev_hash, hash
        FROM events
        WHERE machine_id = ?
        ORDER BY id ASC
        LIMIT ?;
        """,
        (machine_id, max_events),
    )
    rows = cur.fetchall()

    prev_norm = None
    checked = 0

    for r in rows:
        (
            event_id, ts, mid, door_id, event_type, severity, correlation_id,
            sale_id, command_id, old_state, new_state, payload_json, prev_hash, h
        ) = r

        prev_hash_norm = _normalize_hash(prev_hash)
        h_norm = _normalize_hash(h)

        if prev_hash_norm != prev_norm:
            return {
                "ok": False,
                "reason": "prev_hash_mismatch",
                "at_event_id": event_id,
                "events_checked": checked,
                "max_events": max_events,
                "expected_prev_hash": prev_norm,
                "got_prev_hash": prev_hash_norm,
            }

        base = "|".join(
            [
                ts,
                mid,
                str(door_id or ""),
                event_type,
                severity,
                correlation_id,
                sale_id or "",
                command_id or "",
                old_state or "",
                new_state or "",
                payload_json or "{}",
                (prev_hash_norm or "").replace("sha256:", ""),  # compat
                salt,
            ]
        )
        expected_norm = _sha256_prefixed(base)

        if h_norm != expected_norm:
            return {
                "ok": False,
                "reason": "hash_mismatch",
                "at_event_id": event_id,
                "events_checked": checked,
                "max_events": max_events,
                "expected_hash": expected_norm,
                "got_hash": h_norm,
            }

        prev_norm = h_norm
        checked += 1

    return {
        "ok": True,
        "events_checked": checked,
        "max_events": max_events,
        "salt_used": bool(salt),
        "last_hash": prev_norm,
    }


def _calc_severity(chain_ok: bool, snapshot_ok: bool, cfg_ok: bool) -> tuple[str, int]:
    """
    GREEN  = tudo ok
    YELLOW = 1 falha
    RED    = 2+ falhas
    """
    fails = 0
    if not chain_ok:
        fails += 1
    if not snapshot_ok:
        fails += 1
    if not cfg_ok:
        fails += 1

    if fails == 0:
        return ("GREEN", 0)
    if fails == 1:
        return ("YELLOW", 1)
    return ("RED", 2)


def _build_summary(chain: dict, snap: dict, cfg_ok: bool, cfg_reason: str | None) -> str:
    if chain.get("ok") and snap.get("ok") and cfg_ok:
        return "ok"

    parts = []
    if not chain.get("ok"):
        parts.append(f"event_chain {chain.get('reason')}")
    if not snap.get("ok"):
        reason = snap.get("reason") or ("tampered" if snap.get("tampered") else "invalid")
        parts.append(f"snapshot {reason}")
    if not cfg_ok:
        parts.append(f"config {cfg_reason or 'mismatch'}")

    return " | ".join(parts)


@router.api_route("/self_check", methods=["GET", "POST"])
def self_check(
    request: Request,
    machine_id: str = Query(default=None),
    date_utc: str = Query(default=None, description="YYYY-MM-DD (UTC). Se vazio, usa hoje."),
    max_events: int = Query(20000, ge=1, le=50000),
    strict_salt: bool = Query(default=True),
    x_internal_token: str | None = Header(default=None),
):
    """
    Heartbeat antifraude (nível máximo):
    - verifica integridade do event chain (hash chain)
    - verifica integridade do snapshot do dia (arquivo + encadeamento + as-of date)
    - verifica coerência de config_fingerprint (ambiente)
    """
    _require_internal_token(x_internal_token)

    mid = machine_id or DEFAULT_MACHINE_ID
    date = date_utc or _utc_date_str()

    started_at = _utc_now_iso()

    # Check 1: Event chain
    chain = _verify_event_chain(mid, max_events=max_events, strict_salt=strict_salt)

    # Check 2: Snapshot file integrity (histórico “as-of date”)
    snap = verify_snapshot_file(
        machine_id=mid,
        date_utc=date,
        verify_previous=True,
        verify_against_events_db=True,
    )

    # Check 3: config fingerprint
    cfg_current = _config_fingerprint_current(mid)
    cfg_from_snapshot = _read_snapshot_config_fingerprint(mid, date)

    cfg_ok = False
    cfg_reason = None
    if cfg_from_snapshot.get("ok"):
        cfg_ok = (cfg_current["config_fingerprint"] == cfg_from_snapshot["config_fingerprint"])
        if not cfg_ok:
            cfg_reason = "mismatch"
    else:
        cfg_reason = cfg_from_snapshot.get("reason")

    chain_ok = bool(chain.get("ok"))
    snap_ok = bool(snap.get("ok"))

    severity, severity_code = _calc_severity(chain_ok, snap_ok, cfg_ok)
    summary = _build_summary(chain, snap, cfg_ok, cfg_reason)

    checks_ok = chain_ok and snap_ok and cfg_ok

    recommendations = []
    if strict_salt and not os.getenv("LOG_HASH_SALT"):
        recommendations.append("Definir LOG_HASH_SALT (obrigatório para verificação forte).")
    if DEFAULT_MACHINE_ID == "CACIFO-XX-001":
        recommendations.append("Definir MACHINE_ID por serviço (evitar CACIFO-XX-001).")
    if chain_ok is False:
        recommendations.append("ALERTA: Event chain inválido. Rodar /audit/verify detalhado e verificar DB.")
    if snap_ok is False:
        reason = snap.get("reason")
        if reason == "file_not_found":
            recommendations.append("Snapshot do dia não encontrado. Gerar via /audit/snapshot e configurar cron diário.")
        elif reason == "LOG_HASH_SALT_not_set":
            recommendations.append("Snapshot verify falhou por falta de LOG_HASH_SALT.")
        else:
            recommendations.append("Snapshot inválido/adulterado. Checar arquivos em /backups/daily/antifraud.")
    if cfg_ok is False:
        recommendations.append("Config fingerprint não bate com snapshot: verificar EVENT_DB_PATH/BACKUPS_DIR/LOGS_DIR/LOG_HASH_SALT.")

    ended_at = _utc_now_iso()
    stats = _events_stats(mid)
    db_path = _get_events_db_path()

    return {
        "ok": checks_ok,
        "severity": severity,
        "severity_code": severity_code,
        "summary": summary,
        "service": {
            "machine_id": mid,
            "region": REGION,
            "date_utc": date,
        },
        "timestamps": {
            "started_at_utc": started_at,
            "ended_at_utc": ended_at,
        },
        "checks": {
            "event_chain": chain,
            "snapshot_file": snap,
            "config_fingerprint": {
                "current": cfg_current,
                "snapshot": cfg_from_snapshot,
                "match": cfg_ok,
                "reason": cfg_reason,
            },
        },
        "storage": {
            "events_db_path": db_path,
            "backups_dir": os.getenv("BACKUPS_DIR") or ("/backups" if os.path.exists("/backups") else None),
            "logs_dir": os.getenv("LOGS_DIR") or ("/logs" if os.path.exists("/logs") else None),
        },
        "stats": stats,
        "environment": {
            "salt_configured": bool(os.getenv("LOG_HASH_SALT")),
            "salt_fingerprint": _salt_fingerprint(),
            "machine_id_configured": bool(os.getenv("MACHINE_ID")),
            "events_db_path_configured": bool(os.getenv("EVENTS_DB_PATH")),
        },
        "recommendations": recommendations,
        "links": {
            "verify_event_chain": f"/audit/verify?machine_id={mid}&max_events={max_events}",
            "list_events": f"/audit/events?machine_id={mid}&limit=200",
            "snapshot_generate": f"/audit/snapshot?machine_id={mid}",
            "snapshot_verify_file": f"/audit/snapshot/verify_file?machine_id={mid}&date_utc={date}",
            "snapshot_verify_latest": f"/audit/snapshot/verify_latest?machine_id={mid}&days=7",
            "snapshot_create_latest": f"/audit/snapshot/create_latest?machine_id={mid}&days=7",
        },
    }