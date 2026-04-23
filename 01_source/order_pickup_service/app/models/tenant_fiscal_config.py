# Cadastro fiscal por tenant (O-1 Sprint — contrato billing ↔ orders).

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, String

from app.core.db import Base

TZ = DateTime(timezone=True)


class TenantFiscalConfig(Base):
    __tablename__ = "tenant_fiscal_config"

    tenant_id = Column(String(100), primary_key=True)
    cnpj = Column(String(18), nullable=False)
    razao_social = Column(String(140), nullable=False)
    ie = Column(String(20), nullable=True)
    regime = Column(String(20), nullable=False)
    crt = Column(String(1), nullable=False)  # código CRT SEFAZ (1 caractere)
    cert_a1_ref = Column(String(255), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(TZ, nullable=False, default=lambda: datetime.now(timezone.utc))
