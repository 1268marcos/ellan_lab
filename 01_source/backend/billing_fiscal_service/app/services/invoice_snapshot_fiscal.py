# F-1 — Campos fiscais unificados na invoice, derivados do snapshot (order_pickup fiscal-context v2).

from __future__ import annotations

from typing import Any


# Valores alinhados ao backlog Sprint Fiscal (varchar no banco; sem PG ENUM aqui).
FISCAL_DOC_SUBTYPE_NFC_E_65 = "NFC_E_65"
FISCAL_DOC_SUBTYPE_NFE_55 = "NFE_55"
FISCAL_DOC_SUBTYPE_SAFT_PT = "SAFT_PT"
FISCAL_DOC_SUBTYPE_FACTURAE_ES = "FACTURAE_ES"
FISCAL_DOC_SUBTYPE_INVOICE_GENERIC = "INVOICE_GENERIC"

EMISSION_MODE_ONLINE = "ONLINE"
EMISSION_MODE_CONTINGENCY_SVRS = "CONTINGENCY_SVRS"
EMISSION_MODE_OFFLINE_SAT = "OFFLINE_SAT"


def _default_fiscal_doc_subtype(country: str) -> str:
    c = (country or "").strip().upper()
    if c == "BR":
        return FISCAL_DOC_SUBTYPE_NFC_E_65
    if c == "PT":
        return FISCAL_DOC_SUBTYPE_SAFT_PT
    if c == "ES":
        return FISCAL_DOC_SUBTYPE_FACTURAE_ES
    return FISCAL_DOC_SUBTYPE_INVOICE_GENERIC


def fiscal_columns_from_order_snapshot(
    snapshot: dict[str, Any],
    *,
    country: str,
    emission_mode: str = EMISSION_MODE_ONLINE,
) -> dict[str, Any]:
    """
    Monta colunas F-1 a partir do snapshot retornado por get_order_snapshot_for_invoice
    (inclui contract_version v2 quando disponível).
    """
    order = snapshot.get("order") or {}
    pickup = snapshot.get("pickup") or {}
    allocation = snapshot.get("allocation") or {}
    tenant_fiscal = snapshot.get("tenant_fiscal") or {}

    locker_id = snapshot.get("locker_id") or pickup.get("locker_id") or allocation.get("locker_id")
    if locker_id is not None:
        locker_id = str(locker_id).strip() or None

    totem_id = order.get("totem_id")
    if totem_id is not None:
        totem_id = str(totem_id).strip() or None

    slot_raw = pickup.get("slot")
    slot_label = str(slot_raw) if slot_raw is not None else None

    emitter_cnpj = tenant_fiscal.get("cnpj") or snapshot.get("tenant_cnpj")
    if emitter_cnpj is not None:
        emitter_cnpj = str(emitter_cnpj).strip() or None
    emitter_name = tenant_fiscal.get("razao_social") or snapshot.get("tenant_razao_social")
    if emitter_name is not None:
        emitter_name = str(emitter_name).strip() or None

    consumer_cpf = snapshot.get("consumer_cpf")
    if consumer_cpf is not None:
        consumer_cpf = str(consumer_cpf).strip() or None
    consumer_name = snapshot.get("consumer_name")
    if consumer_name is not None:
        consumer_name = str(consumer_name).strip() or None

    profile = snapshot.get("consumer_fiscal_profile") or {}
    if isinstance(profile, dict) and (country or "").strip().upper() == "BR":
        if not consumer_cpf and (profile.get("tax_document_type") or "").strip().upper() == "CPF":
            v = profile.get("tax_document_value")
            if v is not None:
                digits = "".join(ch for ch in str(v) if ch.isdigit())
                consumer_cpf = digits or None

    locker_address = snapshot.get("locker_address")
    if locker_address is not None and not isinstance(locker_address, dict):
        locker_address = None

    raw_items = snapshot.get("order_items")
    lines: list[Any]
    if isinstance(raw_items, list):
        lines = list(raw_items)
    else:
        lines = []

    items_json: dict[str, Any] = {"lines": lines}

    return {
        "locker_id": locker_id,
        "totem_id": totem_id,
        "slot_label": slot_label,
        "fiscal_doc_subtype": _default_fiscal_doc_subtype(country),
        "emission_mode": emission_mode,
        "emitter_cnpj": emitter_cnpj,
        "emitter_name": emitter_name,
        "consumer_cpf": consumer_cpf,
        "consumer_name": consumer_name,
        "locker_address": locker_address,
        "items_json": items_json,
    }
