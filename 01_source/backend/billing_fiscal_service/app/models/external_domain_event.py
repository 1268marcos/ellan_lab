# 01_source/backend/billing_fiscal_service/app/models/external_domain_event.py
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class DomainEvent(Base):
    __tablename__ = "domain_events"

    id: Mapped[str] = mapped_column(primary_key=True)
    aggregate_id: Mapped[str] = mapped_column(String)
    event_name: Mapped[str] = mapped_column(String)