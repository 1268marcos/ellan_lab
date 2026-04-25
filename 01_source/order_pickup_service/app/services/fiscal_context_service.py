"""Contrato versionado v2: contexto fiscal completo para billing_fiscal_service."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.models.allocation import Allocation
from app.models.locker import Locker
from app.models.order import Order
from app.models.pickup import Pickup
from app.models.tenant_fiscal_config import TenantFiscalConfig
from app.models.user import User
from app.services.integration_outbox_service import enqueue_partner_order_paid_event_if_needed
from app.services.ops_audit_service import record_ops_action_audit

logger = logging.getLogger(__name__)

CONTRACT_VERSION = 2
_DEFAULT_NCM = "00000000"
_DEFAULT_ICMS_CST = "90"
_DEFAULT_PIS_CST = "99"
_DEFAULT_COFINS_CST = "99"
_DEFAULT_CFOP = "5102"


def _enum_value_or_raw(value) -> str | None:
    if value is None:
        return None
    return getattr(value, "value", value)


def _metadata_dict(order: Order) -> dict[str, Any]:
    raw = getattr(order, "order_metadata", None) or {}
    return dict(raw) if isinstance(raw, dict) else {}


def extract_consumer_from_order(order: Order) -> tuple[str | None, str | None]:
    meta = _metadata_dict(order)
    cpf = meta.get("consumer_cpf")
    name = meta.get("consumer_name")
    if cpf is not None:
        cpf = str(cpf).strip() or None
    if name is not None:
        name = str(name).strip() or None
    return cpf, name


def _extract_consumer_from_user(user: User | None) -> tuple[str | None, str | None]:
    if not user:
        return None, None
    doc_country = (user.tax_country or "").strip().upper()
    doc_type = (user.tax_document_type or "").strip().upper()
    doc_value = (user.tax_document_value or "").strip()
    if doc_country == "BR" and doc_type == "CPF" and doc_value:
        return doc_value, (user.full_name or None)
    return None, (user.full_name or None)


def _locker_address_dict(locker: Locker | None) -> dict[str, Any] | None:
    if locker is None:
        return None
    addr = locker.to_dict(include_address=True).get("address") or {}
    return {k: v for k, v in addr.items() if v is not None}


def _tenant_fiscal_public(row: TenantFiscalConfig) -> dict[str, Any]:
    return {
        "tenant_id": row.tenant_id,
        "cnpj": row.cnpj,
        "razao_social": row.razao_social,
        "ie": row.ie,
        "regime": row.regime,
        "crt": row.crt,
        "cert_a1_ref": row.cert_a1_ref,
        "is_active": row.is_active,
    }


def _json_load_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


def _to_iso_utc(value: datetime | None) -> str:
    if value is None:
        return datetime.now(timezone.utc).isoformat()
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def _resolve_fiscal_by_product(
    db: Session,
    *,
    sku_id: str,
) -> dict[str, Any] | None:
    row = db.execute(
        text(
            """
            SELECT sku_id, ncm_code, icms_cst, pis_cst, cofins_cst, cfop
            FROM product_fiscal_config
            WHERE sku_id = :sku_id
              AND COALESCE(is_active, TRUE) = TRUE
            """
        ),
        {"sku_id": sku_id},
    ).mappings().first()
    return dict(row) if row else None


def _resolve_fiscal_by_category(
    db: Session,
    *,
    sku_id: str,
) -> dict[str, Any] | None:
    row = db.execute(
        text(
            """
            SELECT p2.id AS sku_id, pfc.ncm_code, pfc.icms_cst, pfc.pis_cst, pfc.cofins_cst, pfc.cfop
            FROM products p
            JOIN products p2 ON p2.category_id = p.category_id
            JOIN product_fiscal_config pfc ON pfc.sku_id = p2.id
            WHERE p.id = :sku_id
              AND p2.id <> :sku_id
              AND COALESCE(pfc.is_active, TRUE) = TRUE
              AND p.category_id IS NOT NULL
            ORDER BY p2.updated_at DESC NULLS LAST, p2.id DESC
            LIMIT 1
            """
        ),
        {"sku_id": sku_id},
    ).mappings().first()
    return dict(row) if row else None


def _resolve_fiscal_defaults() -> dict[str, Any]:
    return {
        "ncm_code": _DEFAULT_NCM,
        "icms_cst": _DEFAULT_ICMS_CST,
        "pis_cst": _DEFAULT_PIS_CST,
        "cofins_cst": _DEFAULT_COFINS_CST,
        "cfop": _DEFAULT_CFOP,
    }


def _fiscal_log_exists(db: Session, *, order_id: str, sku_id: str) -> bool:
    row = db.execute(
        text(
            """
            SELECT id
            FROM fiscal_auto_classification_log
            WHERE order_id = :order_id
              AND sku_id = :sku_id
            ORDER BY id DESC
            LIMIT 1
            """
        ),
        {"order_id": order_id, "sku_id": sku_id},
    ).mappings().first()
    return bool(row)


def _insert_fiscal_auto_classification_log(
    db: Session,
    *,
    order_id: str,
    invoice_id: str | None,
    sku_id: str,
    source: str,
    fiscal: dict[str, Any],
) -> None:
    if _fiscal_log_exists(db, order_id=order_id, sku_id=sku_id):
        return
    db.execute(
        text(
            """
            INSERT INTO fiscal_auto_classification_log (
                order_id, invoice_id, sku_id, ncm_applied, icms_cst_applied, pis_cst_applied,
                cofins_cst_applied, cfop_applied, source, classified_at
            ) VALUES (
                :order_id, :invoice_id, :sku_id, :ncm_applied, :icms_cst_applied, :pis_cst_applied,
                :cofins_cst_applied, :cfop_applied, :source, NOW()
            )
            """
        ),
        {
            "order_id": order_id,
            "invoice_id": invoice_id,
            "sku_id": sku_id,
            "ncm_applied": fiscal.get("ncm_code"),
            "icms_cst_applied": fiscal.get("icms_cst"),
            "pis_cst_applied": fiscal.get("pis_cst"),
            "cofins_cst_applied": fiscal.get("cofins_cst"),
            "cfop_applied": fiscal.get("cfop"),
            "source": source,
        },
    )


def _record_default_fiscal_alert(
    db: Session,
    *,
    order_id: str,
    sku_id: str,
) -> None:
    record_ops_action_audit(
        db=db,
        action="PR3_FISCAL_CLASSIFICATION_DEFAULT_ALERT",
        result="ERROR",
        correlation_id=f"corr-pr3-fiscal-{uuid4().hex}",
        role="system",
        order_id=order_id,
        details={
            "order_id": order_id,
            "sku_id": sku_id,
            "source": "DEFAULT",
            "message": "Classificação fiscal caiu em DEFAULT; revisar configuração por SKU/categoria.",
            "ts": _to_iso_utc(datetime.now(timezone.utc)),
        },
    )


def _apply_auto_fiscal_classification(
    db: Session,
    *,
    order: Order,
    items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    source_counter: dict[str, int] = {}
    for raw_item in items:
        item = dict(raw_item or {})
        sku_id = str(item.get("sku_id") or "").strip()
        if not sku_id:
            out.append(item)
            continue

        resolved = _resolve_fiscal_by_product(db, sku_id=sku_id)
        source = "AUTO_PRODUCT_CONFIG"
        if not resolved:
            resolved = _resolve_fiscal_by_category(db, sku_id=sku_id)
            source = "CATEGORY_FALLBACK"
        if not resolved:
            resolved = _resolve_fiscal_defaults()
            source = "DEFAULT"

        item["fiscal_classification"] = {
            "source": source,
            "ncm": resolved.get("ncm_code"),
            "icms_cst": resolved.get("icms_cst"),
            "pis_cst": resolved.get("pis_cst"),
            "cofins_cst": resolved.get("cofins_cst"),
            "cfop": resolved.get("cfop"),
        }
        source_counter[source] = int(source_counter.get(source, 0) or 0) + 1

        _insert_fiscal_auto_classification_log(
            db,
            order_id=order.id,
            invoice_id=None,
            sku_id=sku_id,
            source=source,
            fiscal=resolved,
        )
        if source == "DEFAULT":
            _record_default_fiscal_alert(db, order_id=order.id, sku_id=sku_id)

        out.append(item)

    if out:
        event_payload = {
            "order_id": order.id,
            "sources": source_counter,
            "items_count": len(out),
            "event_origin": "fiscal_context_auto_classification",
            "event_ts": _to_iso_utc(datetime.now(timezone.utc)),
        }
        outbox_row, idempotent = enqueue_partner_order_paid_event_if_needed(
            db,
            order_id=order.id,
            payload=event_payload,
        )
        record_ops_action_audit(
            db=db,
            action="I1_ORDER_FISCAL_OUTBOX_ENQUEUE",
            result="SUCCESS",
            correlation_id=f"corr-i1-outbox-{uuid4().hex}",
            role="system",
            order_id=order.id,
            details={
                "order_id": order.id,
                "idempotent": idempotent,
                "event_type": "ORDER_PAID",
                "partner_id": outbox_row.get("partner_id"),
                "outbox_id": outbox_row.get("id"),
                "sources": source_counter,
                "ts": _to_iso_utc(datetime.now(timezone.utc)),
            },
        )

    return out


def resolve_effective_tenant_id(order: Order, locker: Locker | None) -> str | None:
    tid = getattr(order, "tenant_id", None)
    if tid and str(tid).strip():
        return str(tid).strip()
    if locker and locker.tenant_id and str(locker.tenant_id).strip():
        return str(locker.tenant_id).strip()
    return None


def resolve_order_fiscal_emit_fields(
    db: Session,
    order: Order,
    allocation: Allocation | None,
    pickup: Pickup | None,
) -> tuple[str | None, str | None, str | None, str | None]:
    """
    tenant_id efetivo, CNPJ do tenant (se cadastrado), CPF/nome consumidor.
    Usado na fila order.paid (payload v2).
    """
    locker_id = None
    if allocation and allocation.locker_id:
        locker_id = allocation.locker_id
    elif pickup and pickup.locker_id:
        locker_id = pickup.locker_id
    locker = db.query(Locker).filter(Locker.id == locker_id).first() if locker_id else None
    effective_tenant_id = resolve_effective_tenant_id(order, locker)
    tenant_cnpj = None
    bind = db.get_bind()
    if bind is not None and inspect(bind).has_table("tenant_fiscal_config") and effective_tenant_id:
        row = (
            db.query(TenantFiscalConfig)
            .filter(TenantFiscalConfig.tenant_id == effective_tenant_id)
            .filter(TenantFiscalConfig.is_active.is_(True))
            .first()
        )
        if row:
            tenant_cnpj = row.cnpj
    consumer_cpf, consumer_name = extract_consumer_from_order(order)
    if getattr(order, "user_id", None):
        user = db.query(User).filter(User.id == order.user_id).first()
        user_cpf, user_name = _extract_consumer_from_user(user)
        consumer_cpf = consumer_cpf or user_cpf
        consumer_name = consumer_name or user_name
    return effective_tenant_id, tenant_cnpj, consumer_cpf, consumer_name


def build_fiscal_context(db: Session, order_id: str) -> dict[str, Any]:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise ValueError("order_not_found")

    allocation = db.query(Allocation).filter(Allocation.order_id == order.id).first()
    pickup = (
        db.query(Pickup)
        .filter(Pickup.order_id == order.id)
        .order_by(Pickup.created_at.desc())
        .first()
    )

    locker_id = None
    if allocation and allocation.locker_id:
        locker_id = allocation.locker_id
    elif pickup and pickup.locker_id:
        locker_id = pickup.locker_id

    locker = db.query(Locker).filter(Locker.id == locker_id).first() if locker_id else None

    effective_tenant_id = resolve_effective_tenant_id(order, locker)

    tenant_fiscal = None
    tenant_cnpj = None
    tenant_razao = None
    bind = db.get_bind()
    if bind is not None and inspect(bind).has_table("tenant_fiscal_config"):
        if effective_tenant_id:
            row = (
                db.query(TenantFiscalConfig)
                .filter(TenantFiscalConfig.tenant_id == effective_tenant_id)
                .filter(TenantFiscalConfig.is_active.is_(True))
                .first()
            )
            if row:
                tenant_fiscal = _tenant_fiscal_public(row)
                tenant_cnpj = row.cnpj
                tenant_razao = row.razao_social

    consumer_cpf, consumer_name = extract_consumer_from_order(order)
    user = None
    if getattr(order, "user_id", None):
        user = db.query(User).filter(User.id == order.user_id).first()
        user_cpf, user_name = _extract_consumer_from_user(user)
        consumer_cpf = consumer_cpf or user_cpf
        consumer_name = consumer_name or user_name

    items: list[dict[str, Any]] = []
    try:
        for it in order.items or []:
            items.append(it.to_dict())
    except Exception as exc:
        logger.warning("fiscal_context_order_items_failed order_id=%s err=%s", order.id, exc)

    if not items and getattr(order, "sku_id", None):
        items.append(
            {
                "order_id": order.id,
                "sku_id": order.sku_id,
                "sku_description": getattr(order, "sku_description", None),
                "ncm": None,
                "quantity": 1,
                "unit_amount_cents": order.amount_cents,
                "total_amount_cents": order.amount_cents,
                "item_status": "CONFIRMED",
                "metadata": {},
            }
        )
    items = _apply_auto_fiscal_classification(db, order=order, items=items)
    db.commit()

    order_out = {
        "id": order.id,
        "user_id": getattr(order, "user_id", None),
        "channel": _enum_value_or_raw(order.channel),
        "region": order.region,
        "totem_id": order.totem_id,
        "sku_id": getattr(order, "sku_id", None),
        "status": _enum_value_or_raw(order.status),
        "amount_cents": order.amount_cents,
        "currency": (order.currency or "BRL").strip().upper(),
        "payment_method": _enum_value_or_raw(order.payment_method),
        "payment_status": _enum_value_or_raw(order.payment_status),
        "paid_at": order.paid_at.isoformat() if order.paid_at else None,
        "pickup_deadline_at": order.pickup_deadline_at.isoformat() if order.pickup_deadline_at else None,
        "picked_up_at": order.picked_up_at.isoformat() if order.picked_up_at else None,
        "gateway_transaction_id": getattr(order, "gateway_transaction_id", None),
        "tenant_id": effective_tenant_id,
        "receipt_email": getattr(order, "receipt_email", None),
        "receipt_phone": getattr(order, "receipt_phone", None),
        "order_metadata": _metadata_dict(order),
    }

    allocation_out = None
    if allocation:
        allocation_out = {
            "id": allocation.id,
            "locker_id": allocation.locker_id,
            "slot": allocation.slot,
            "state": _enum_value_or_raw(allocation.state),
        }

    pickup_out = None
    if pickup:
        pickup_out = {
            "id": pickup.id,
            "locker_id": pickup.locker_id,
            "machine_id": pickup.machine_id,
            "slot": pickup.slot,
            "status": _enum_value_or_raw(pickup.status),
        }

    return {
        "contract_version": CONTRACT_VERSION,
        "order": order_out,
        "order_items": items,
        "allocation": allocation_out,
        "pickup": pickup_out,
        "locker_id": locker_id,
        "locker_address": _locker_address_dict(locker),
        "tenant_fiscal": tenant_fiscal,
        "tenant_cnpj": tenant_cnpj,
        "tenant_razao_social": tenant_razao,
        "consumer_cpf": consumer_cpf,
        "consumer_name": consumer_name,
        "consumer_fiscal_profile": {
            "tax_country": user.tax_country if user else None,
            "tax_document_type": user.tax_document_type if user else None,
            "tax_document_value": user.tax_document_value if user else None,
            "fiscal_email": user.fiscal_email if user else None,
            "fiscal_phone": user.fiscal_phone if user else None,
            "fiscal_address_line1": user.fiscal_address_line1 if user else None,
            "fiscal_address_line2": user.fiscal_address_line2 if user else None,
            "fiscal_address_city": user.fiscal_address_city if user else None,
            "fiscal_address_state": user.fiscal_address_state if user else None,
            "fiscal_address_postal_code": user.fiscal_address_postal_code if user else None,
            "fiscal_address_country": user.fiscal_address_country if user else None,
            "fiscal_data_consent": bool(user.fiscal_data_consent) if user else False,
        },
    }
