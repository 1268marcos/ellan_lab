"""Gate de dados do destinatário antes de emissão em provedor real (F-3 / domínio usuário fiscal)."""

from __future__ import annotations
def build_test_consumer_profile(*, country: str, complete: bool = True) -> dict:
    """
    Utilitário para gerar payloads de perfil fiscal do consumidor para testes.

    Args:
        country (str): Código do país ("BR" ou "PT").
        complete (bool): Se True, retorna todos os campos obrigatórios preenchidos.
                         Se False, retorna um payload mínimo/vazio para testar falhas.

    Returns:
        dict: Payload de perfil fiscal conforme solicitado.

    Raises:
        ValueError: Se o país não for reconhecido.
    """
    normalized_country = str(country or "").strip().upper()
    if normalized_country not in {"BR", "PT"}:
        raise ValueError(f"País fiscal não suportado para testes: {country!r}")

    if not complete:
        # Payload vazio/minimalista para testar rejeição/falha do gate
        return {
            "fiscal_data_consent": False,
            "tax_country": normalized_country,
            # Demais campos propositalmente ausentes ou inválidos
        }

    if normalized_country == "BR":
        doc_type, doc_value = "CPF", "12345678901"
        addr_state = "SP"
        addr_postal = "01001-000"
        addr_country = "BR"
    else:  # PT
        doc_type, doc_value = "NIF", "123456789"
        addr_state = None  # Portugal não exige estado
        addr_postal = "1000-001"
        addr_country = "PT"

    profile = {
        "fiscal_data_consent": True,
        "tax_country": normalized_country,
        "tax_document_type": doc_type,
        "tax_document_value": doc_value,
        "fiscal_email": "cliente+test@exemplo.com",
        "fiscal_address_line1": "Av. Teste, 100",
        "fiscal_address_city": "Cidade Teste",
        "fiscal_address_state": addr_state,
        "fiscal_address_postal_code": addr_postal,
        "fiscal_address_country": addr_country,
    }
    # Remover None para campos não aplicáveis
    return {k: v for k, v in profile.items() if v is not None}

# Exemplos de uso em testes unitários:

def test_build_test_consumer_profile_br_complete():
    p = build_test_consumer_profile(country="BR", complete=True)
    assert p["tax_country"] == "BR"
    assert p["tax_document_type"] == "CPF"
    assert len(p["tax_document_value"]) == 11
    assert p["fiscal_email"] == "cliente+test@exemplo.com"

def test_build_test_consumer_profile_pt_incomplete():
    p = build_test_consumer_profile(country="PT", complete=False)
    assert p["tax_country"] == "PT"
    assert not p["fiscal_data_consent"]
    assert "tax_document_value" not in p

def test_invalid_country_raises():
    import pytest
    with pytest.raises(ValueError):
        build_test_consumer_profile(country="ES")

# Como injetar no order_snapshot para testes de integração:
# 
# order_snapshot = {
#     "order": {
#         # ... outros campos ...
#         "consumer_profile": build_test_consumer_profile(country="BR", complete=True)
#     }
# }
# 
# Exemplo: invoice = claim_and_process_invoice_by_id(session, order_id, order_snapshot=order_snapshot)

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
