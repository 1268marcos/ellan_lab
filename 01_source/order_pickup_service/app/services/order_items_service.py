# CRUD de order_items (uso interno + apoio à criação de pedido).

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.order_item import OrderItem
from app.schemas.order_items import OrderItemCreateIn, OrderItemPatchIn, normalize_ncm_optional


def _get_order_or_404(db: Session, order_id: str) -> Order:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail={"type": "ORDER_NOT_FOUND", "order_id": order_id})
    return order


def _get_item_or_404(db: Session, order_id: str, item_id: int) -> OrderItem:
    row = (
        db.query(OrderItem)
        .filter(OrderItem.id == item_id, OrderItem.order_id == order_id)
        .first()
    )
    if not row:
        raise HTTPException(
            status_code=404,
            detail={"type": "ORDER_ITEM_NOT_FOUND", "order_id": order_id, "item_id": item_id},
        )
    return row


def insert_primary_line_if_absent(
    db: Session,
    *,
    order: Order,
    sku_id: str,
    amount_cents: int,
    sku_description: str | None = None,
    order_line_ncm: str | None = None,
) -> OrderItem | None:
    """
    Garante uma linha em order_items para pedidos single-SKU (fiscal / NCM).
    Não duplica se já existir item para o pedido.
    """
    exists = db.query(OrderItem).filter(OrderItem.order_id == order.id).first()
    if exists:
        return None
    ncm: str | None = None
    if order_line_ncm:
        ncm = normalize_ncm_optional(str(order_line_ncm).strip())
    row = OrderItem(
        order_id=order.id,
        sku_id=sku_id,
        sku_description=sku_description,
        ncm=ncm,
        quantity=1,
        unit_amount_cents=int(amount_cents),
        total_amount_cents=int(amount_cents),
        item_status="PENDING",
        metadata_json={},
    )
    db.add(row)
    return row


def list_order_items(db: Session, order_id: str) -> list[OrderItem]:
    _get_order_or_404(db, order_id)
    return (
        db.query(OrderItem)
        .filter(OrderItem.order_id == order_id)
        .order_by(OrderItem.id.asc())
        .all()
    )


def create_order_item(db: Session, order_id: str, payload: OrderItemCreateIn) -> OrderItem:
    _get_order_or_404(db, order_id)
    row = OrderItem(
        order_id=order_id,
        sku_id=payload.sku_id,
        sku_description=payload.sku_description,
        ncm=payload.ncm,
        quantity=payload.quantity,
        unit_amount_cents=payload.unit_amount_cents,
        total_amount_cents=payload.total_amount_cents or (payload.quantity * payload.unit_amount_cents),
        slot_preference=payload.slot_preference,
        slot_size=payload.slot_size,
        item_status=payload.item_status or "PENDING",
        metadata_json=dict(payload.metadata or {}),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def patch_order_item(db: Session, order_id: str, item_id: int, payload: OrderItemPatchIn) -> OrderItem:
    _get_order_or_404(db, order_id)
    row = _get_item_or_404(db, order_id, item_id)
    data = payload.model_dump(exclude_unset=True)

    if "ncm" in data:
        row.ncm = data["ncm"]
    if "sku_description" in data:
        row.sku_description = data["sku_description"]
    if "slot_preference" in data:
        row.slot_preference = data["slot_preference"]
    if "slot_size" in data:
        row.slot_size = data["slot_size"]
    if "item_status" in data and data["item_status"] is not None:
        row.item_status = data["item_status"]
    if "metadata" in data and data["metadata"] is not None:
        row.metadata_json = dict(data["metadata"])

    qty = row.quantity
    unit = row.unit_amount_cents
    if "quantity" in data and data["quantity"] is not None:
        qty = int(data["quantity"])
        row.quantity = qty
    if "unit_amount_cents" in data and data["unit_amount_cents"] is not None:
        unit = int(data["unit_amount_cents"])
        row.unit_amount_cents = unit

    if "total_amount_cents" in data and data["total_amount_cents"] is not None:
        row.total_amount_cents = int(data["total_amount_cents"])
    elif "quantity" in data or "unit_amount_cents" in data:
        row.total_amount_cents = qty * unit

    db.commit()
    db.refresh(row)
    return row
