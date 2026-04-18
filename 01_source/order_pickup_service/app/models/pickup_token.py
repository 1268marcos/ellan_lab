# 01_source/order_pickup_service/app/models/pickup_token.py
# pickup_tokens - credenciais temporárias de retirada
# 17/04/2026 - inclusão de manual_code
# 17/04/2026 - suporte a manual_code_encrypted com fallback legado manual_code

from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from datetime import datetime

from app.core.db import Base


class PickupToken(Base):
    __tablename__ = "pickup_tokens"

    id = Column(String, primary_key=True)  # uuid
    pickup_id = Column(String, ForeignKey("pickups.id"), nullable=False)

    token_hash = Column(String, nullable=False)

    # legado temporário: manter para leitura de tokens antigos
    manual_code = Column(String, nullable=True)

    # novo padrão seguro
    manual_code_encrypted = Column(String, nullable=True)

    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_pickup_tokens_pickup_id", "pickup_id"),
        Index("ix_pickup_tokens_token_hash", "token_hash"),
    )

