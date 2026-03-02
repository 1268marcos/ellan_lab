from __future__ import annotations

from typing import Any, Dict, Optional

from app.core.hashing import canonical_json, sha256_prefixed
from app.core.event_log import GatewayEventLogger


def _extract_block_count(snapshot: Dict[str, Any]) -> int:
    try:
        decisions = snapshot.get("stats", {}).get("decisions", {}) or {}
        return int(decisions.get("BLOCK", 0))
    except Exception:
        return 0


def _extract_fail_rate(snapshot: Dict[str, Any]) -> float:
    try:
        integrity = snapshot.get("integrity", {}) or {}
        r = integrity.get("reasons_json_parse", {}) or {}
        return float(r.get("fail_rate", 0.0))
    except Exception:
        return 0.0


def _compute_severity(snapshot: Dict[str, Any]) -> Dict[str, str]:
    """
    Regra simples e objetiva:
      - HIGH: existe ao menos 1 BLOCK
      - MEDIUM: fail_rate > 0 (integridade ruim) e sem BLOCK
      - INFO: ok
    """
    block_count = _extract_block_count(snapshot)
    fail_rate = _extract_fail_rate(snapshot)

    if block_count > 0:
        return {"severity": "HIGH", "severity_code": "SNAPSHOT_BLOCKS_PRESENT"}
    if fail_rate > 0:
        return {"severity": "MEDIUM", "severity_code": "SNAPSHOT_INTEGRITY_WARN"}
    return {"severity": "INFO", "severity_code": "SNAPSHOT_OK"}


def verify_snapshot(
    *,
    snapshot: Dict[str, Any],
    logger: GatewayEventLogger,
    expected_config_fingerprint: str,
) -> Dict[str, Any]:
    """
    Verifica:
      1) snapshot_hash bate com recalculado
      2) log_anchor aponta para um log verificável (se existir)
      3) last_hash do log (se houver) bate com anchor (quando verificação ok)
      4) config_fingerprint do snapshot bate com o esperado (config ativa)
    E retorna severity.
    """
    if not snapshot:
        return {"ok": False, "status": "empty_snapshot"}

    stored_hash = snapshot.get("snapshot_hash")
    if not stored_hash:
        return {"ok": False, "status": "missing_snapshot_hash"}

    # recalcula hash do core (sem snapshot_hash)
    core = dict(snapshot)
    core.pop("snapshot_hash", None)

    computed = sha256_prefixed(canonical_json(core))
    if computed != stored_hash:
        return {
            "ok": False,
            "status": "snapshot_hash_mismatch",
            "stored_hash": stored_hash,
            "computed_hash": computed,
        }

    # config binding
    snap_cfg = (snapshot.get("fingerprints") or {}).get("config_fingerprint")
    config_ok = (snap_cfg == expected_config_fingerprint)

    # log anchor verify
    anchor = snapshot.get("log_anchor") or {}
    ymd = anchor.get("log_date")
    if not ymd:
        return {"ok": False, "status": "missing_log_anchor_date"}

    log_verify = logger.verify_chain(ymd)

    # se não existe log no dia, OK (sem eventos)
    if log_verify.get("status") == "missing_file":
        sev = _compute_severity(snapshot)
        return {
            "ok": True,
            "status": "verified_no_log_file",
            "snapshot_hash": stored_hash,
            "config_binding": {
                "ok": config_ok,
                "expected": expected_config_fingerprint,
                "snapshot": snap_cfg,
            },
            "log_verify": log_verify,
            **sev,
        }

    if not log_verify.get("ok"):
        sev = _compute_severity(snapshot)
        return {
            "ok": False,
            "status": "log_chain_invalid",
            "snapshot_hash": stored_hash,
            "config_binding": {
                "ok": config_ok,
                "expected": expected_config_fingerprint,
                "snapshot": snap_cfg,
            },
            "log_verify": log_verify,
            **sev,
        }

    # se log ok e tem last_hash, valida
    anchor_last = anchor.get("last_hash")
    log_last = log_verify.get("last_hash")
    if anchor_last and log_last and anchor_last != log_last:
        sev = _compute_severity(snapshot)
        return {
            "ok": False,
            "status": "log_anchor_mismatch",
            "snapshot_hash": stored_hash,
            "config_binding": {
                "ok": config_ok,
                "expected": expected_config_fingerprint,
                "snapshot": snap_cfg,
            },
            "anchor_last_hash": anchor_last,
            "log_last_hash": log_last,
            "log_verify": log_verify,
            **sev,
        }

    sev = _compute_severity(snapshot)

    # se config não bate, isso não invalida o hash do snapshot,
    # mas é um ALERTA forte de auditoria.
    status = "verified" if config_ok else "verified_config_mismatch"

    return {
        "ok": True,
        "status": status,
        "snapshot_hash": stored_hash,
        "config_binding": {
            "ok": config_ok,
            "expected": expected_config_fingerprint,
            "snapshot": snap_cfg,
        },
        "log_verify": log_verify,
        **sev,
    }