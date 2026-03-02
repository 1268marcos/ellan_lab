# 01_source/order_pickup_service/app/models/kiosk_antifraud_event.py
import uuid
from sqlalchemy import Column, String, DateTime
from app.models.base import Base

class KioskAntifraudEvent(Base):
    __tablename__ = "kiosk_antifraud_events"

    id = Column(String, primary_key=True)
    fp_hash = Column(String, nullable=False, index=True)
    ip_hash = Column(String, nullable=False, index=True)
    totem_id = Column(String, nullable=False)
    region = Column(String, nullable=False)

    created_at = Column(DateTime, nullable=False)
    blocked_until = Column(DateTime, nullable=True)

    @staticmethod
    def new(fp_hash: str, ip_hash: str, totem_id: str, region: str, created_at, blocked_until):
        obj = KioskAntifraudEvent()
        obj.id = str(uuid.uuid4())
        obj.fp_hash = fp_hash
        obj.ip_hash = ip_hash
        obj.totem_id = totem_id
        obj.region = region
        obj.created_at = created_at
        obj.blocked_until = blocked_until
        return obj