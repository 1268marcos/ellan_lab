# 01_source/backend/billing_fiscal_service/app/integrations/lifecycle_client.py
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.external_domain_event import DomainEvent


def has_payment_approved(db: Session, order_id: str) -> bool:
    stmt = select(DomainEvent).where(
        DomainEvent.aggregate_id == order_id,
        DomainEvent.event_name == "PAYMENT_APPROVED",
    )
    result = db.execute(stmt).first()
    return result is not None