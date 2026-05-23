from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Integer, Numeric, String, Text

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class FinanceLockerNetworkCatalog(Base):
    __tablename__ = "finance_locker_network_catalog"

    id = Column(String(36), primary_key=True)
    code = Column(String(48), nullable=False, unique=True, index=True)
    name = Column(String(160), nullable=False)
    player_role = Column(String(40), nullable=False)
    parent_group = Column(String(40), nullable=False)
    segment_code = Column(String(40), nullable=True, index=True)
    country_code = Column(String(2), nullable=False)
    regions_json = Column(Text, nullable=False, default="[]")
    supports_lockers = Column(Boolean, nullable=False, default=True)
    supports_marketplace = Column(Boolean, nullable=False, default=False)
    supports_collection_points = Column(Boolean, nullable=False, default=False)
    supports_food_delivery = Column(Boolean, nullable=False, default=False)
    integration_modes_json = Column(Text, nullable=False, default="[]")
    global_tier = Column(String(20), nullable=False, default="REGIONAL")
    locker_operator_ref = Column(String(48), nullable=True)
    default_billing_model = Column(String(30), nullable=False, default="HYBRID")
    default_revenue_share_pct = Column(Numeric(6, 4), nullable=True)
    monthly_fee_cents = Column(BigInteger, nullable=True)
    integration_status = Column(String(20), nullable=False, default="PLANNED")
    estimated_locker_count = Column(Integer, nullable=True)
    finance_partner_id = Column(String(36), nullable=True, index=True)
    api_docs_url = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)
    sort_order = Column(Integer, nullable=False, default=100)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)

    @property
    def regions(self) -> list[str]:
        try:
            return json.loads(self.regions_json or "[]")
        except json.JSONDecodeError:
            return []
