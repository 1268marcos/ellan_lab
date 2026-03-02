# pickup_tokens (QR) - Armazenar hash, uso único
from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from datetime import datetime
from app.models.base import Base

class PickupToken(Base):
    __tablename__ = "pickup_tokens"
    id = Column(String, primary_key=True)  # uuid
    order_id = Column(String, ForeignKey("orders.id"), nullable=False)

    token_hash = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_pickup_tokens_order_id", "order_id"),
        Index("ix_pickup_tokens_token_hash", "token_hash"),
    )

# acima (trecho)