# 01_source/backend/billing_fiscal_service/app/workers/invoice_worker.py
# veja como exemplo - # 01_source/backend/order_lifecycle_service/app/workers/prepayment_timeout_worker.py
import time
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.services.invoice_service import generate_invoice
from app.models.external_domain_event import DomainEvent

logger = logging.getLogger("invoice_worker")

POLL_INTERVAL = 5


def process_events(db: Session):
    stmt = (
        select(DomainEvent)
        .where(DomainEvent.event_name == "PAYMENT_APPROVED")
        .limit(50)
    )

    events = db.execute(stmt).scalars().all()

    for event in events:
        order_id = event.aggregate_id

        try:
            generate_invoice(db, order_id)
            logger.info(f"[OK] invoice criada order_id={order_id}")
        except Exception as e:
            logger.warning(f"[ERRO] order_id={order_id} erro={str(e)}")


def run():
    logger.info("Invoice worker iniciado")

    while True:
        db = SessionLocal()
        try:
            process_events(db)
        finally:
            db.close()

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    run()