# Catálogo fiscal por SKU (F-2) — NCM, CSTs, categoria IVA PT.

from __future__ import annotations

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ProductFiscalConfig(Base):
    __tablename__ = "product_fiscal_config"

    sku_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    ncm_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    cest: Mapped[str | None] = mapped_column(String(9), nullable=True)
    icms_cst: Mapped[str | None] = mapped_column(String(3), nullable=True)
    pis_cst: Mapped[str | None] = mapped_column(String(2), nullable=True)
    cofins_cst: Mapped[str | None] = mapped_column(String(2), nullable=True)
    iva_category: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
