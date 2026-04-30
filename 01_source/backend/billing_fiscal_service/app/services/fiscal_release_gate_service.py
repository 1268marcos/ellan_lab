"""RELEASE-GATE-01 — leitura consolidada de flags fiscais por ambiente (BR/PT).

Não altera configuração; apenas expõe estado atual para decisão explícita
stub vs real e rollback via variáveis de ambiente (documentado no checklist).
"""
from __future__ import annotations

from app.core.config import settings


def build_fiscal_release_gate_payload() -> dict:
    br_real = bool(settings.fiscal_real_provider_br_enabled)
    pt_real = bool(settings.fiscal_real_provider_pt_enabled)
    a1_dry = bool(settings.fiscal_a1_dry_run_enabled)
    smtp = bool(settings.invoice_smtp_enabled)

    risks: list[str] = []
    if br_real and not settings.fiscal_real_provider_base_url_br:
        risks.append("BR_REAL_ENABLED_SEM_BASE_URL_BR")
    if pt_real and not settings.fiscal_real_provider_base_url_pt:
        risks.append("PT_REAL_ENABLED_SEM_BASE_URL_PT")
    if br_real and pt_real:
        risks.append("AMBOS_PROVIDERS_REAIS_ATIVOS_REVISAR_CAPACIDADE")

    return {
        "scope": "RELEASE_GATE_FISCAL_ENV",
        "providers": {
            "BR": {
                "real_provider_enabled": br_real,
                "base_url_configured": bool(str(settings.fiscal_real_provider_base_url_br or "").strip()),
                "timeout_sec": settings.fiscal_real_provider_timeout_sec,
                "retries": settings.fiscal_real_provider_retries,
            },
            "PT": {
                "real_provider_enabled": pt_real,
                "base_url_configured": bool(str(settings.fiscal_real_provider_base_url_pt or "").strip()),
                "timeout_sec": settings.fiscal_real_provider_timeout_sec,
                "retries": settings.fiscal_real_provider_retries,
            },
        },
        "a1_dry_run": {
            "enabled": a1_dry,
            "cert_ref": settings.fiscal_a1_dry_run_cert_ref,
            "hmac_secret_configured": bool(str(settings.fiscal_a1_dry_run_hmac_secret or "").strip()),
        },
        "invoice_email_smtp_enabled": smtp,
        "stub_only_recommended": not (br_real or pt_real),
        "risk_flags": risks,
        "rollback_hints": {
            "disable_br_real": "FISCAL_REAL_PROVIDER_BR_ENABLED=false",
            "disable_pt_real": "FISCAL_REAL_PROVIDER_PT_ENABLED=false",
            "disable_a1_dry_run": "FISCAL_A1_DRY_RUN_ENABLED=false",
            "disable_smtp": "INVOICE_SMTP_ENABLED=false",
        },
    }
