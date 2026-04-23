"""Contrato versionado v2: contexto fiscal completo para billing_fiscal_service."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.models.allocation import Allocation
from app.models.locker import Locker
from app.models.order import Order
from app.models.pickup import Pickup
from app.models.tenant_fiscal_config import TenantFiscalConfig

logger = logging.getLogger(__name__)

CONTRACT_VERSION = 2


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
    }
