import os
import sqlite3
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Query, Request

from app.core.db import get_conn
from app.core.event_log import _sha256
from app.core.antifraud_snapshot_verify import verify_snapshot_file

router = APIRouter(prefix="/audit", tags=["audit"])


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _utc_date_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _default_machine_id(request: Request) -> str:
    env_mid = os.getenv("MACHINE_ID")
    if env_mid:
        return env_mid

    port = request.url.port if request.url else None
    if port == 8101:
        return "CACIFO-SP-001"
    if port == 8102:
        return "CACIFO-PT-001"

    return "CACIFO-PT-001"


# Fingerprint atual
def _config_fingerprint_current(machine_id: str) -> dict:
    salt = os.getenv("LOG_HASH_SALT", "")
    events_db_path = os.getenv("EVENTS_DB_PATH")

    salt_fp = _sha256(salt) if salt else None

    payload = json.dumps(
        {
            "machine_id": machine_id,
            "events_db_path": events_db_path,
            "salt_fingerprint": salt_fp,
        },
        sort_keys=True,
        separators=(",", ":"),
    )

    cfg_fp = _sha256(payload)

    return {
        "machine_id": machine_id,
        "events_db_path": events_db_path,
        "salt_fingerprint": salt_fp,
        "config_fingerprint": cfg_fp,
    }


# Caminho do snapshot do dia
def _snapshot_path_for_date(machine_id: str, date_utc: str) -> str:
    home = str(Path.home())
    root = f"{home}/ellan_lab"
    return str(Path(root) / "05_backups" / "daily" / "antifraud" / f"{machine_id}_{date_utc}.json")


# Ler config_fingerprint do snapshot (sem depender do verify)
def _read_snapshot_config_fingerprint(machine_id: str, date_utc: str) -> dict:
    path = _snapshot_path_for_date(machine_id, date_utc)
    p = Path(path)
    if not p.exists():
        return {"ok": False, "reason": "snapshot_file_not_found", "path": path}

    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        return {"ok": False, "reason": "snapshot_invalid_json", "path": path, "detail": str(e)}

    cfg = data.get("config_fingerprint")
    if not cfg:
        return {"ok": False, "reason": "snapshot_config_fingerprint_missing", "path": path}

    return {"ok": True, "path": path, "config_fingerprint": cfg}


def _calc_severity(chain_ok: bool, snapshot_ok: bool):
    """
    GREEN  = ambos ok
    YELLOW = 1 falha
    RED    = ambos falham
    """
    if chain_ok and snapshot_ok:
        return ("GREEN", 0)
    if (chain_ok and not snapshot_ok) or (not chain_ok and snapshot_ok):
        return ("YELLOW", 1)
    return ("RED", 2)


def _build_summary(chain: dict, snap: dict) -> str:
    """
    Texto curto (ideal pra dashboard/heartbeat).
    Prioriza o problema mais crítico.
    """
    chain_ok = bool(chain.get("ok"))
    snap_ok = bool(snap.get("ok"))

    if chain_ok and snap_ok:
        return "ok"

    parts = []
    if not chain_ok:
        # ex.: hash_mismatch / prev_hash_mismatch
        reason = chain.get("reason") or "invalid"
        at_id = chain.get("at_event_id")
        if at_id is not None:
            parts.append(f"event_chain {reason} at_event_id={at_id}")
        else:
            parts.append(f"event_chain {reason}")

    if not snap_ok:
        reason = snap.get("reason") or ("tampered" if snap.get("tampered") else "invalid")
        if reason == "file_not_found":
            parts.append("snapshot missing")
        elif reason == "LOG_HASH_SALT_not_set":
            parts.append("snapshot verify no_salt")
        elif snap.get("tampered") is True:
            parts.append("snapshot tampered")
        else:
            parts.append(f"snapshot {reason}")

    return " | ".join(parts)


def _get_events_db_path() -> str | None:
    # prioridade: ENV (mais correto)
    env_path = os.getenv("EVENTS_DB_PATH")
    if env_path:
        return env_path

    # fallback: tenta inferir do objeto connection (nem sempre existe)
    try:
        conn = get_conn()
        # pragma database_list retorna o caminho do arquivo principal (SQLite)
        row = conn.execute("PRAGMA database_list;").fetchone()
        if row and len(row) >= 3:
            # row = (seq, name, file)
            return row[2]
    except Exception:
        pass

    return None


def _salt_fingerprint() -> str | None:
    salt = os.getenv("LOG_HASH_SALT", "")
    if not salt:
        return None
    # fingerprint sem expor o salt (sha256 do salt)
    return _sha256(salt)


def _events_stats(machine_id: str) -> dict:
    conn = get_conn()

    total = conn.execute(
        "SELECT COUNT(1) FROM events WHERE machine_id = ?;",
        (machine_id,),
    ).fetchone()[0]

    first = conn.execute(
        "SELECT id, ts FROM events WHERE machine_id = ? ORDER BY id ASC LIMIT 1;",
        (machine_id,),
    ).fetchone()

    last = conn.execute(
        "SELECT id, ts FROM events WHERE machine_id = ? ORDER BY id DESC LIMIT 1;",
        (machine_id,),
    ).fetchone()

    return {
        "events_total": int(total),
        "first_event": {"id": first[0], "ts": first[1]} if first else None,
        "last_event": {"id": last[0], "ts": last[1]} if last else None,
        "bootstrap": (int(total) == 0),
    }


def _verify_event_chain(machine_id: str, max_events: int):
    """
    Verificador interno do event log (equivalente ao /audit/verify).
    Retorna dict detalhado.
    """
    conn = get_conn()
    salt = os.getenv("LOG_HASH_SALT", "")

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

    prev = None
    checked = 0
    for r in rows:
        (
            _id, ts, mid, door_id, event_type, severity, correlation_id,
            sale_id, command_id, old_state, new_state, payload_json, prev_hash, h
        ) = r

        if prev_hash != prev:
            return {
                "ok": False,
                "reason": "prev_hash_mismatch",
                "at_event_id": _id,
                "events_checked": checked,
                "max_events": max_events,
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
                payload_json,
                prev_hash or "",
                salt,  # se salt vazio, ainda valida de forma consistente (mas fraco)
            ]
        )
        expected = _sha256(base)

        if expected != h:
            return {
                "ok": False,
                "reason": "hash_mismatch",
                "at_event_id": _id,
                "events_checked": checked,
                "max_events": max_events,
            }

        prev = h
        checked += 1

    # pega último id/hash para referência rápida
    last = None
    cur_last = conn.execute(
        "SELECT id, ts, hash FROM events WHERE machine_id = ? ORDER BY id DESC LIMIT 1;",
        (machine_id,),
    )
    row_last = cur_last.fetchone()
    if row_last:
        last = {"id": row_last[0], "ts": row_last[1], "hash": row_last[2]}

    return {
        "ok": True,
        "events_checked": checked,
        "max_events": max_events,
        "salt_used": bool(salt),
        "last_event": last,
    }


# endpoint
@router.api_route("/self_check", methods=["GET", "POST"])
def self_check(
    request: Request,
    machine_id: str = Query(None),
    date_utc: str = Query(None, description="YYYY-MM-DD (UTC). Se vazio, usa hoje."),
    max_events: int = Query(20000, ge=1, le=200000),
):
    """
    Heartbeat antifraude (profissional):
    - verifica integridade do event chain (logs)
    - verifica integridade do snapshot do dia (arquivo)
    - retorna status geral + recomendações
    """
    mid = machine_id or _default_machine_id(request)
    date = date_utc or _utc_date_str()

    started_at = _utc_now_iso()

    # Check 1: Event chain
    chain = _verify_event_chain(mid, max_events=max_events)

    # Check 2: Snapshot file integrity
    snap = verify_snapshot_file(machine_id=mid, date_utc=date)

    cfg_current = _config_fingerprint_current(mid)
    cfg_from_snapshot = _read_snapshot_config_fingerprint(mid, date)

    cfg_match = False
    cfg_reason = None
    if cfg_from_snapshot.get("ok"):
        cfg_match = (cfg_current["config_fingerprint"] == cfg_from_snapshot["config_fingerprint"])
        if not cfg_match:
            cfg_reason = "mismatch"
    else:
        cfg_reason = cfg_from_snapshot.get("reason")

    chain_ok = bool(chain.get("ok"))
    snap_ok = bool(snap.get("ok"))

    severity, severity_code = _calc_severity(chain_ok, snap_ok)
    summary = _build_summary(chain, snap)

    # Se a config não bate com o snapshot do dia, eleva severidade e melhora summary
    if cfg_match is False:
        if severity_code == 0:
            severity, severity_code = ("YELLOW", 1)
        if summary == "ok":
            summary = "config mismatch with snapshot"
        else:
            summary = summary + " | config mismatch with snapshot"

    # status global continua sendo o "ambos ok"
    # checks_ok = chain_ok and snap_ok

    # Status global
    # checks_ok = bool(chain.get("ok")) and bool(snap.get("ok"))

    # status global (ambos ok) vers.2 ELIMINAR ACIMA
    checks_ok = chain_ok and snap_ok

    # Recomendações automáticas (úteis pra operação)
    recommendations = []
    if not os.getenv("LOG_HASH_SALT"):
        recommendations.append("Definir LOG_HASH_SALT (obrigatório para segurança antifraude).")
    if not os.getenv("MACHINE_ID"):
        recommendations.append("Definir MACHINE_ID por serviço para evitar fallback por porta.")
    if chain.get("ok") is False:
        recommendations.append("ALERTA: Event chain inválido. Rodar /audit/verify detalhado e verificar DB.")
    if snap.get("ok") is False:
        reason = snap.get("reason")
        if reason == "file_not_found":
            recommendations.append("Snapshot do dia não encontrado. Gerar via /audit/snapshot e configurar cron diário.")
        elif reason == "LOG_HASH_SALT_not_set":
            recommendations.append("Snapshot verify falhou por falta de LOG_HASH_SALT.")
        else:
            recommendations.append("Snapshot inválido ou adulterado. Checar arquivos em 05_backups/daily/antifraud.")

    ended_at = _utc_now_iso()

    stats = _events_stats(mid)
    db_path = _get_events_db_path()

    salt_fp = _salt_fingerprint()
    salt_cfg = bool(os.getenv("LOG_HASH_SALT"))

    # Payload profissional e completo
    return {
        "ok": checks_ok,
        "severity": severity,
        "severity_code": severity_code,
        "summary": summary,
        "service": {
            "machine_id": mid,
            "port": request.url.port if request.url else None,
            "date_utc": date,
        },
        "timestamps": {
            "started_at_utc": started_at,
            "ended_at_utc": ended_at,
        },
        "checks": {
            "event_chain": chain,
            "snapshot_file": snap,
        },
        "storage": {
            "events_db_path": db_path,
        },
        "stats": {
            **stats
        },
        "environment": {
            "salt_configured": salt_cfg,
            "salt_fingerprint": salt_fp,  # NÃO expõe o salt
            "machine_id_configured": bool(os.getenv("MACHINE_ID")),
            "events_db_path_configured": bool(os.getenv("EVENTS_DB_PATH")),
        },
        "config": {
            "current": cfg_current,
            "snapshot": cfg_from_snapshot,
            "match": cfg_match,
            "reason": cfg_reason,
        },
        "recommendations": recommendations,
        "links": {
            "verify_event_chain": f"/audit/verify?machine_id={mid}&max_events={max_events}",
            "snapshot_generate": f"/audit/snapshot?machine_id={mid}",
            "snapshot_verify_file": f"/audit/snapshot/verify_file?machine_id={mid}&date_utc={date}",
        },
    }