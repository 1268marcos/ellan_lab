from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.partner import EcommercePartner, LogisticsPartner
from app.services.crypto_util import new_id
from app.services.order_ops_service import seed_demo_order_graph


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def run_seed(db: Session) -> dict[str, int]:
    counts = {"ecommerce": 0, "logistics": 0, "orders": 0}
    now = _utcnow()

    if not db.query(EcommercePartner).filter(EcommercePartner.code == "DEMO-EC-OPS").first():
        db.add(
            EcommercePartner(
                id="ec-ops-001",
                name="OPS E-commerce Pickup",
                code="DEMO-EC-OPS",
                integration_type="REST",
                api_base_url="https://api.ops-pickup.example/v1",
                sla_pickup_hours=48,
                active=True,
                country="BR",
                status="ACTIVE",
                support_email="pickup-ops@ellanlab.com",
                created_at=now,
                updated_at=now,
            )
        )
        counts["ecommerce"] += 1

    if not db.query(LogisticsPartner).filter(LogisticsPartner.code == "DEMO-LG-OPS").first():
        db.add(
            LogisticsPartner(
                id="lg-ops-001",
                name="OPS Logistica Pickup",
                code="DEMO-LG-OPS",
                integration_type="REST",
                api_base_url="https://logistics.ops-pickup.example",
                default_sla_hours=48,
                active=True,
                country="BR",
                created_at=now,
                updated_at=now,
            )
        )
        counts["logistics"] += 1

    db.commit()
    seed_demo_order_graph(db, partner_id="ec-ops-001")
    counts["orders"] = 1
    return counts
