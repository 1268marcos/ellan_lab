from __future__ import annotations

import os

from app.core.config import settings
from app.services.fiscal_fg1_stub_service import FG1_WAVE_COUNTRIES, build_fg1_coverage_gate


def _env_bool(name: str, default: bool = False) -> bool:
    value = str(os.getenv(name, "")).strip().lower()
    if not value:
        return default
    return value in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    raw = str(os.getenv(name, "")).strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _is_auth_configured(country_code: str) -> bool:
    prefix = f"FISCAL_FG1_{country_code}_"
    auth_mode = str(os.getenv(f"{prefix}AUTH_MODE", "")).strip().upper()
    if not auth_mode:
        return False
    if auth_mode == "API_KEY":
        return bool(str(os.getenv(f"{prefix}API_KEY", "")).strip())
    if auth_mode == "OAUTH2":
        return bool(str(os.getenv(f"{prefix}CLIENT_ID", "")).strip()) and bool(
            str(os.getenv(f"{prefix}CLIENT_SECRET", "")).strip()
        )
    if auth_mode == "CERTIFICATE":
        return bool(str(os.getenv(f"{prefix}CERT_REF", "")).strip())
    return False


def _readiness_row(country_code: str, coverage_country_status: str) -> dict:
    prefix = f"FISCAL_FG1_{country_code}_"
    timeout_sec = _env_int(f"{prefix}TIMEOUT_SEC", settings.fiscal_real_provider_timeout_sec)
    retries = _env_int(f"{prefix}RETRIES", settings.fiscal_real_provider_retries)
    sla_timeout_retry_ok = timeout_sec <= 10 and retries <= 3
    auth_configured = _is_auth_configured(country_code)
    homologation_approved = _env_bool(f"{prefix}HOMOLOGATION_APPROVED", default=False)
    certificate_ready = _env_bool(f"{prefix}CERTIFICATE_READY", default=False)

    checks = [
        {"code": "auth", "label": "Auth configurado", "status": "OK" if auth_configured else "BLOCKED"},
        {
            "code": "homologation",
            "label": "Homologação aprovada",
            "status": "OK" if homologation_approved else "BLOCKED",
        },
        {
            "code": "certificate",
            "label": "Certificado pronto/validado",
            "status": "OK" if certificate_ready else "BLOCKED",
        },
        {
            "code": "sla_timeout_retry",
            "label": "SLA timeout/retry dentro da política",
            "status": "OK" if sla_timeout_retry_ok else "BLOCKED",
            "details": {"timeout_sec": timeout_sec, "retries": retries},
        },
        {
            "code": "coverage_gate",
            "label": "Coverage gate sem cenários faltantes",
            "status": "OK" if coverage_country_status == "GO" else "BLOCKED",
        },
    ]
    blocking_reasons = [
        {
            "code": check["code"],
            "label": check["label"],
            "details": check.get("details", {}),
        }
        for check in checks
        if check["status"] != "OK"
    ]
    return {
        "country_code": country_code,
        "readiness_status": "GO" if len(blocking_reasons) == 0 else "NO_GO",
        "checks": checks,
        "blocking_reasons": blocking_reasons,
    }


def build_fg1_readiness_gate() -> dict:
    coverage_gate = build_fg1_coverage_gate()
    coverage_by_country = {
        str(item.get("country_code")): str(item.get("coverage_status", "NO_GO"))
        for item in coverage_gate.get("countries", [])
    }

    countries = []
    blocking_reasons_total = 0
    for country_code in FG1_WAVE_COUNTRIES:
        readiness = _readiness_row(country_code, coverage_by_country.get(country_code, "NO_GO"))
        blocking_reasons_total += len(readiness["blocking_reasons"])
        countries.append(readiness)

    return {
        "wave": "FG-1-WAVE-1",
        "gate_version": "fg1-readiness-gate-v1",
        "decision": "GO" if blocking_reasons_total == 0 else "NO_GO",
        "blocking_reasons_total": blocking_reasons_total,
        "country_count": len(countries),
        "countries": countries,
    }


def build_fg1_readiness_action_plan() -> dict:
    gate = build_fg1_readiness_gate()
    items = []
    for row in gate.get("countries", []):
        country_code = str(row.get("country_code") or "").upper()
        if not country_code:
            continue
        blocking_reasons = row.get("blocking_reasons") or []
        env_prefix = f"FISCAL_FG1_{country_code}_"
        required_env_keys = []
        actions = []
        for reason in blocking_reasons:
            code = str(reason.get("code") or "").strip().lower()
            if code == "auth":
                required_env_keys.extend(
                    [
                        f"{env_prefix}AUTH_MODE",
                        f"{env_prefix}API_KEY|{env_prefix}CLIENT_ID/{env_prefix}CLIENT_SECRET|{env_prefix}CERT_REF",
                    ]
                )
                actions.append("Configurar método de autenticação e credenciais do país.")
            elif code == "homologation":
                required_env_keys.append(f"{env_prefix}HOMOLOGATION_APPROVED")
                actions.append("Concluir homologação com autoridade fiscal e aprovar no ambiente.")
            elif code == "certificate":
                required_env_keys.append(f"{env_prefix}CERTIFICATE_READY")
                actions.append("Provisionar/validar certificado digital em vault e runtime.")
            elif code == "sla_timeout_retry":
                required_env_keys.extend([f"{env_prefix}TIMEOUT_SEC", f"{env_prefix}RETRIES"])
                actions.append("Ajustar timeout/retries para política operacional (timeout<=10, retries<=3).")
            elif code == "coverage_gate":
                actions.append("Corrigir cobertura canônica de cenários antes de go-live real.")

        dedup_required_env = sorted(set(required_env_keys))
        dedup_actions = []
        for action in actions:
            if action not in dedup_actions:
                dedup_actions.append(action)
        items.append(
            {
                "country_code": country_code,
                "status": row.get("readiness_status"),
                "blocking_reasons_count": len(blocking_reasons),
                "required_env_keys": dedup_required_env,
                "recommended_actions": dedup_actions,
            }
        )

    return {
        "wave": gate.get("wave", "FG-1-WAVE-1"),
        "plan_version": "fg1-readiness-action-plan-v1",
        "decision": gate.get("decision", "NO_GO"),
        "country_count": len(items),
        "items": items,
    }
