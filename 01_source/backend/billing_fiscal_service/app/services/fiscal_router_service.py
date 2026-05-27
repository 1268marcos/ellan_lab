# Análise da configuração atual do Billing Fiscal Service para roteamento fiscal.

import json

def analyze_fiscal_router_config():
    """
    Analisa a configuração atual do Billing Fiscal Service e responde:
    1. Providers reais habilitados (valores e URLs base configuradas)
    2. Stubs ativos atualmente roteados
    3. Modos de contingência suportados pelo emission_mode/roteador
    4. Release gate (risk_flags atuais)
    
    Retorna um dicionário (e printa em JSON) com esses dados.
    """
    from app.core.config import settings

    # 1. Providers reais habilitados e URLs base
    environment = getattr(settings, "app_env", "dev")
    providers_real = {
        "FISCAL_REAL_PROVIDER_BR_ENABLED": getattr(settings, "fiscal_real_provider_br_enabled", False),
        "FISCAL_REAL_PROVIDER_PT_ENABLED": getattr(settings, "fiscal_real_provider_pt_enabled", False),
        "BR_BASE_URL_CONFIGURED": (
            hasattr(settings, "sefaz_br_base_url")
            and isinstance(settings.sefaz_br_base_url, str)
            and len(settings.sefaz_br_base_url.strip()) > 0
        ) if hasattr(settings, "sefaz_br_base_url") else False,
        "PT_BASE_URL_CONFIGURED": (
            hasattr(settings, "at_pt_base_url")
            and isinstance(settings.at_pt_base_url, str)
            and len(settings.at_pt_base_url.strip()) > 0
        ) if hasattr(settings, "at_pt_base_url") else False,
    }

    # 2. Stubs ativos
    active_stubs = []
    if not providers_real["FISCAL_REAL_PROVIDER_BR_ENABLED"]:
        active_stubs.append("sefaz_sp_service")
    if not providers_real["FISCAL_REAL_PROVIDER_PT_ENABLED"]:
        active_stubs.append("at_pt_service")
    # Sempre disponível:
    active_stubs.append("aeat_es_service")

    # 3. Modos de contingência suportados
    contingency_supported = {
        "OFFLINE_SAT": True,
        "CONTINGENCY_SVRS": True,
        "route_issue_invoice_handles": True,  # Função route_issue_invoice prevê ambos
    }

    # 4. Release Gate (risk_flags)
    def build_fiscal_release_gate_payload():
        risk_flags = []
        if not providers_real["FISCAL_REAL_PROVIDER_BR_ENABLED"]:
            risk_flags.append("BR_STUB")
        if not providers_real["FISCAL_REAL_PROVIDER_PT_ENABLED"]:
            risk_flags.append("PT_STUB")
        # Modos de contingência são fallback, não risk_flags
        return risk_flags

    release_gate = {
        "risk_flags": build_fiscal_release_gate_payload()
    }

    # 5. Recomendação de uso real x stub
    has_real = providers_real["FISCAL_REAL_PROVIDER_BR_ENABLED"] or providers_real["FISCAL_REAL_PROVIDER_PT_ENABLED"]
    recommendation = (
        "Habilitar provider real para produção" if not has_real else
        "Providers reais ativos, ok para produção"
    )

    result = {
        "environment": environment,
        "providers_real": providers_real,
        "active_stubs": active_stubs,
        "contingency_supported": contingency_supported,
        "release_gate": release_gate,
        "recommendation": recommendation,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result
from app.core.config import settings

def analyze_fiscal_router_config():
    # 1. Providers Reais Habilitados
    environment = getattr(settings, "app_env", "dev")
    providers_real = {
        "FISCAL_REAL_PROVIDER_BR_ENABLED": getattr(settings, "fiscal_real_provider_br_enabled", False),
        "FISCAL_REAL_PROVIDER_PT_ENABLED": getattr(settings, "fiscal_real_provider_pt_enabled", False),
        "FISCAL_REAL_PROVIDER_BR_URL": getattr(settings, "fiscal_real_provider_br_url", None),
        "FISCAL_REAL_PROVIDER_PT_URL": getattr(settings, "fiscal_real_provider_pt_url", None),
    }

    # 2. Stubs Ativos
    # O roteador direciona para stubs se os providers reais estiverem desabilitados.
    active_stubs = []
    if not providers_real["FISCAL_REAL_PROVIDER_BR_ENABLED"]:
        active_stubs.append("sefaz_sp_service")
    if not providers_real["FISCAL_REAL_PROVIDER_PT_ENABLED"]:
        active_stubs.append("at_pt_service")
    active_stubs.append("aeat_es_service")  # ES não tem provider real implementado
    # Contingência comum no BR: stub de contingência (offline)

    # 3. Modo de Contingência
    contingency_supported = {
        "OFFLINE_SAT": True,
        "CONTINGENCY_SVRS": True,
        "route_issue_invoice_handles": True, # vide função route_issue_invoice
    }

    # 4. Release Gate
    def build_fiscal_release_gate_payload():
        risk_flags = []
        if not providers_real["FISCAL_REAL_PROVIDER_BR_ENABLED"]:
            risk_flags.append("BR_STUB")
        if not providers_real["FISCAL_REAL_PROVIDER_PT_ENABLED"]:
            risk_flags.append("PT_STUB")
        # Contingência é tratada como fallback, não flag específica
        return risk_flags

    release_gate = {
        "risk_flags": build_fiscal_release_gate_payload()
    }

    # 5. Recomendação
    has_real = providers_real["FISCAL_REAL_PROVIDER_BR_ENABLED"] or providers_real["FISCAL_REAL_PROVIDER_PT_ENABLED"]
    recommendation = (
        "Habilitar provider real para produção" if not has_real else
        "Providers reais ativos, ok para produção"
    )

    result = {
        "environment": environment,
        "providers_real": providers_real,
        "active_stubs": active_stubs,
        "contingency_supported": contingency_supported,
        "release_gate": release_gate,
        "recommendation": recommendation,
    }

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result

# Exemplo de uso (descomente para rodar standalone):
# analyze_fiscal_router_config()
from __future__ import annotations

from app.core.config import settings
from app.models.invoice_model import Invoice
from app.services.aeat_es_service import (
    aeat_es_cancel_invoice,
    aeat_es_cc_e_stub,
    aeat_es_issue_invoice,
)
from app.services.at_pt_real_adapter import (
    cancel_invoice_real_or_fallback as at_cancel_real_or_fallback,
    correction_event_real_or_fallback as at_correction_real_or_fallback,
    issue_invoice_real_or_fallback as at_issue_real_or_fallback,
)
from app.services.at_pt_service import at_pt_cancel_invoice, at_pt_cc_e_stub, at_pt_issue_invoice
from app.services.sefaz_sp_service import sefaz_sp_cancel_invoice, sefaz_sp_cc_e_stub, sefaz_sp_issue_invoice
from app.services.sefaz_contingency_service import issue_invoice_contingency_stub
from app.services.sefaz_svrs_real_adapter import (
    cancel_invoice_real_or_fallback as svrs_cancel_real_or_fallback,
    cce_event_real_or_fallback as svrs_cce_real_or_fallback,
    issue_invoice_real_or_fallback as svrs_issue_real_or_fallback,
)


def route_issue_invoice(invoice: Invoice) -> dict:
    country = str(invoice.country or "").strip().upper()
    emission_mode = str(invoice.emission_mode or "").strip().upper()

    if country == "BR":
        if emission_mode in {"OFFLINE_SAT", "CONTINGENCY_SVRS"}:
            return issue_invoice_contingency_stub(invoice)
        if settings.fiscal_real_provider_br_enabled:
            return svrs_issue_real_or_fallback(invoice)
        return sefaz_sp_issue_invoice(invoice)

    if country == "PT":
        if settings.fiscal_real_provider_pt_enabled:
            return at_issue_real_or_fallback(invoice)
        return at_pt_issue_invoice(invoice)

    if country == "ES":
        return aeat_es_issue_invoice(invoice)

    raise ValueError(f"País não suportado para emissão fiscal: {country}")


def route_issue_invoice_reconnect(invoice: Invoice) -> dict:
    """
    Fluxo de re-sync pós contingência:
    tenta autorização oficial sem reaplicar o stub de contingência.
    """
    country = str(invoice.country or "").strip().upper()

    if country == "BR":
        if settings.fiscal_real_provider_br_enabled:
            return svrs_issue_real_or_fallback(invoice)
        return sefaz_sp_issue_invoice(invoice)

    if country == "PT":
        if settings.fiscal_real_provider_pt_enabled:
            return at_issue_real_or_fallback(invoice)
        return at_pt_issue_invoice(invoice)

    if country == "ES":
        return aeat_es_issue_invoice(invoice)

    raise ValueError(f"País não suportado para re-sync fiscal: {country}")


def route_cancel_invoice(invoice: Invoice) -> dict:
    country = str(invoice.country or "").strip().upper()

    if country == "BR":
        if settings.fiscal_real_provider_br_enabled:
            return svrs_cancel_real_or_fallback(invoice)
        return sefaz_sp_cancel_invoice(invoice)

    if country == "PT":
        if settings.fiscal_real_provider_pt_enabled:
            return at_cancel_real_or_fallback(invoice)
        return at_pt_cancel_invoice(invoice)

    if country == "ES":
        return aeat_es_cancel_invoice(invoice)

    raise ValueError(f"País não suportado para cancelamento fiscal: {country}")


def route_cc_e_stub(invoice: Invoice, correction_text: str | None) -> dict:
    country = str(invoice.country or "").strip().upper()

    if country == "BR":
        if settings.fiscal_real_provider_br_enabled:
            return svrs_cce_real_or_fallback(invoice, correction_text)
        return sefaz_sp_cc_e_stub(invoice, correction_text)

    if country == "PT":
        if settings.fiscal_real_provider_pt_enabled:
            return at_correction_real_or_fallback(invoice, correction_text)
        return at_pt_cc_e_stub(invoice, correction_text)

    if country == "ES":
        return aeat_es_cc_e_stub(invoice, correction_text)

    raise ValueError(f"País não suportado para CC-e / correção fiscal: {country}")
