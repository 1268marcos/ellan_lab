from __future__ import annotations

from sqlalchemy import exists, func, select
from sqlalchemy.orm import Query, Session

from app.models.core_order import CoreOrder
from app.models.lifecycle import AnalyticsFact

# Pedidos sem parceiro (ecommerce_partner_id IS NULL) são agrupados sob este id nos filtros.
UNASSIGNED_ECOMMERCE_PARTNER_ID = "unassigned"


def apply_partner_filter(db: Session, query: Query, partner_id: str | None) -> Query:
    if partner_id is None or not str(partner_id).strip():
        return query
    pid = str(partner_id).strip()
    partner_rows = select(1).select_from(CoreOrder).where(
        CoreOrder.id == AnalyticsFact.order_id,
        func.coalesce(
            CoreOrder.ecommerce_partner_id,
            UNASSIGNED_ECOMMERCE_PARTNER_ID,
        )
        == pid,
    )
    return query.filter(exists(partner_rows))
