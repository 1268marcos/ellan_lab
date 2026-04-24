"""Gate de dados do destinatário antes de emissão em provedor real (F-3 / domínio usuário fiscal)."""

from __future__ import annotations

from typing import Any

from app.core.config import settings
from app.models.invoice_model import Invoice


class ConsumerFiscalIncompleteError(Exception):
    """Pedido sem dados mínimos de consumidor para emissão em provedor real."""


def _payload_skips_consumer_gate(invoice: Invoice) -> bool:
    pj = invoice.payload_json or {}
    if not isinstance(pj, dict):
        return False
    if pj.get("skip_consumer_fiscal_gate"):
        return True
    if pj.get("stub_scenario"):
        return True
    if pj.get("smoke_svrs_batch_async"):
        return True
    return False


def uses_real_fiscal_route(invoice: Invoice) -> bool:
    country = str(invoice.country or "").strip().upper()
    emission_mode = str(invoice.emission_mode or "").strip().upper()
    if country == "BR":
        if emission_mode in {"OFFLINE_SAT", "CONTINGENCY_SVRS"}:
            return False
        return bool(settings.fiscal_real_provider_br_enabled)
    if country == "PT":
        return bool(settings.fiscal_real_provider_pt_enabled)
    return False


def _digits_only(s: str) -> str:
    return "".join(ch for ch in str(s or "") if ch.isdigit())


def _profile_complete_for_country(profile: dict[str, Any], *, country: str) -> bool:
    if not profile.get("fiscal_data_consent"):
        return False
    if (str(profile.get("tax_country") or "").strip().upper() != country):
        return False
    doc_type = str(profile.get("tax_document_type") or "").strip().upper()
    if country == "BR" and doc_type != "CPF":
        return False
    if country == "PT" and doc_type != "NIF":
        return False
    required = (
        "tax_document_value",
        "fiscal_email",
        "fiscal_address_line1",
        "fiscal_address_city",
        "fiscal_address_state",
        "fiscal_address_postal_code",
        "fiscal_address_country",
    )
    for key in required:
        if not str(profile.get(key) or "").strip():
            return False
    if country == "BR" and len(_digits_only(str(profile.get("tax_document_value") or ""))) != 11:
        return False
    if country == "PT" and len(_digits_only(str(profile.get("tax_document_value") or ""))) != 9:
        return False
    return True


def _legacy_br_complete(snapshot: dict[str, Any]) -> bool:
    cpf_digits = _digits_only(str(snapshot.get("consumer_cpf") or ""))
    if len(cpf_digits) != 11:
        return False
    name = str(snapshot.get("consumer_name") or "").strip()
    if not name:
        return False
    order = snapshot.get("order") or {}
    email = str(order.get("receipt_email") or order.get("guest_email") or "").strip()
    return bool(email)


def order_snapshot_consumer_ready_for_real(snapshot: dict[str, Any] | None, *, country: str) -> bool:
    """
    True se o snapshot tem dados suficientes para emissão real:
    - perfil fiscal completo em consumer_fiscal_profile (consentimento + campos), ou
    - legado BR: CPF + nome + e-mail no pedido.
    """
    if not isinstance(snapshot, dict):
        return False
    c = (country or "").strip().upper()
    profile = snapshot.get("consumer_fiscal_profile")
    if isinstance(profile, dict) and _profile_complete_for_country(profile, country=c):
        return True
    if c == "BR":
        return _legacy_br_complete(snapshot)
    if c == "PT":
        return isinstance(profile, dict) and _profile_complete_for_country(profile, country="PT")
    return True


def assert_consumer_fiscal_ready_for_real_issue(invoice: Invoice) -> None:
    if not settings.fiscal_require_complete_consumer_for_real_issue:
        return
    if _payload_skips_consumer_gate(invoice):
        return
    if not uses_real_fiscal_route(invoice):
        return
    snap = invoice.order_snapshot if isinstance(invoice.order_snapshot, dict) else {}
    country = str(invoice.country or "BR").strip().upper()
    if order_snapshot_consumer_ready_for_real(snap, country=country):
        return
    raise ConsumerFiscalIncompleteError(
        "consumer_fiscal_incomplete: dados do destinatário insuficientes para emissão em provedor real "
        f"(country={country}). Complete o perfil fiscal no checkout ou use legado BR (CPF+nome+e-mail no pedido)."
    )
