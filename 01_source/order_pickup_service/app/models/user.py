# 01_source/order_pickup_service/app/models/user.py

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    tax_country: Mapped[str | None] = mapped_column(String(2), nullable=True)
    tax_document_type: Mapped[str | None] = mapped_column(String(16), nullable=True)
    tax_document_value: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    fiscal_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    fiscal_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    fiscal_address_line1: Mapped[str | None] = mapped_column(String(255), nullable=True)
    fiscal_address_line2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    fiscal_address_city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    fiscal_address_state: Mapped[str | None] = mapped_column(String(120), nullable=True)
    fiscal_address_postal_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    fiscal_address_country: Mapped[str | None] = mapped_column(String(2), nullable=True)
    fiscal_profile_updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    fiscal_data_consent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    phone_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    auth_sessions: Mapped[list["AuthSession"]] = relationship(
        "AuthSession",
        back_populates="user",
        cascade="all, delete-orphan",
    )