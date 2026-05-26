from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.types import BigIntPK, JsonType


class CapabilityChannel(Base):
    __tablename__ = "capability_channel"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    contexts: Mapped[list["CapabilityContext"]] = relationship(back_populates="channel", cascade="all, delete-orphan")
    profiles: Mapped[list["CapabilityProfile"]] = relationship(back_populates="channel")


class CapabilityContext(Base):
    __tablename__ = "capability_context"
    __table_args__ = (
        UniqueConstraint("channel_id", "code", name="uq_capability_context_channel_code"),
        Index("ix_capability_context_channel", "channel_id"),
    )

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    channel_id: Mapped[int] = mapped_column(BigIntPK, ForeignKey("capability_channel.id", ondelete="RESTRICT"), nullable=False)
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    channel: Mapped["CapabilityChannel"] = relationship(back_populates="contexts")
    profiles: Mapped[list["CapabilityProfile"]] = relationship(back_populates="context")


class CapabilityRegion(Base):
    __tablename__ = "capability_region"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    country_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    continent: Mapped[str | None] = mapped_column(String(60), nullable=True)
    default_currency: Mapped[str] = mapped_column(String(10), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    metadata_json: Mapped[dict] = mapped_column(JsonType, nullable=False, default=dict, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    profiles: Mapped[list["CapabilityProfile"]] = relationship(back_populates="region")


class PaymentMethodCatalog(Base):
    __tablename__ = "payment_method_catalog"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    family: Mapped[str | None] = mapped_column(String(80), nullable=True)
    is_wallet: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    is_card: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    is_bnpl: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    is_cash_like: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    is_bank_transfer: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    is_instant: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    metadata_json: Mapped[dict] = mapped_column(JsonType, nullable=False, default=dict, server_default="{}")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class PaymentInterfaceCatalog(Base):
    __tablename__ = "payment_interface_catalog"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    interface_type: Mapped[str | None] = mapped_column(String(60), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JsonType, nullable=False, default=dict, server_default="{}")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class WalletProviderCatalog(Base):
    __tablename__ = "wallet_provider_catalog"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JsonType, nullable=False, default=dict, server_default="{}")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class CapabilityRequirementCatalog(Base):
    __tablename__ = "capability_requirement_catalog"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    data_type: Mapped[str] = mapped_column(String(40), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class CapabilityProfile(Base):
    __tablename__ = "capability_profile"
    __table_args__ = (
        UniqueConstraint("region_id", "channel_id", "context_id", name="uq_capability_profile_region_channel_context"),
        Index("ix_capability_profile_region", "region_id"),
        Index("ix_capability_profile_channel", "channel_id"),
        Index("ix_capability_profile_context", "context_id"),
    )

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    region_id: Mapped[int] = mapped_column(BigIntPK, ForeignKey("capability_region.id", ondelete="RESTRICT"), nullable=False)
    channel_id: Mapped[int] = mapped_column(BigIntPK, ForeignKey("capability_channel.id", ondelete="RESTRICT"), nullable=False)
    context_id: Mapped[int] = mapped_column(BigIntPK, ForeignKey("capability_context.id", ondelete="RESTRICT"), nullable=False)
    profile_code: Mapped[str] = mapped_column(String(160), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100, server_default="100")
    currency: Mapped[str] = mapped_column(String(10), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    metadata_json: Mapped[dict] = mapped_column(JsonType, nullable=False, default=dict, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    region: Mapped["CapabilityRegion"] = relationship(back_populates="profiles")
    channel: Mapped["CapabilityChannel"] = relationship(back_populates="profiles")
    context: Mapped["CapabilityContext"] = relationship(back_populates="profiles")
    actions: Mapped[list["CapabilityProfileAction"]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    methods: Mapped[list["CapabilityProfileMethod"]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    constraints: Mapped[list["CapabilityProfileConstraint"]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    targets: Mapped[list["CapabilityProfileTarget"]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    snapshots: Mapped[list["CapabilityProfileSnapshot"]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    webhooks: Mapped[list["CapabilityProfileWebhook"]] = relationship(  # noqa: F821
        "CapabilityProfileWebhook", back_populates="profile", cascade="all, delete-orphan"
    )
    api_keys: Mapped[list["CapabilityProfileApiKey"]] = relationship(  # noqa: F821
        "CapabilityProfileApiKey", back_populates="profile", cascade="all, delete-orphan"
    )


class CapabilityProfileAction(Base):
    __tablename__ = "capability_profile_action"
    __table_args__ = (UniqueConstraint("profile_id", "action_code", name="uq_capability_profile_action"),)

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(BigIntPK, ForeignKey("capability_profile.id", ondelete="CASCADE"), nullable=False)
    action_code: Mapped[str] = mapped_column(String(80), nullable=False)
    label: Mapped[str] = mapped_column(String(120), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=100, server_default="100")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    config_json: Mapped[dict] = mapped_column(JsonType, nullable=False, default=dict, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    profile: Mapped["CapabilityProfile"] = relationship(back_populates="actions")


class CapabilityProfileMethod(Base):
    __tablename__ = "capability_profile_method"
    __table_args__ = (UniqueConstraint("profile_id", "payment_method_id", name="uq_capability_profile_method"),)

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(BigIntPK, ForeignKey("capability_profile.id", ondelete="CASCADE"), nullable=False)
    payment_method_id: Mapped[int] = mapped_column(BigIntPK, ForeignKey("payment_method_catalog.id", ondelete="RESTRICT"), nullable=False)
    label: Mapped[str | None] = mapped_column(String(120), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=100, server_default="100")
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    wallet_provider_id: Mapped[int | None] = mapped_column(BigIntPK, ForeignKey("wallet_provider_catalog.id", ondelete="RESTRICT"), nullable=True)
    rules_json: Mapped[dict] = mapped_column(JsonType, nullable=False, default=dict, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    profile: Mapped["CapabilityProfile"] = relationship(back_populates="methods")


class CapabilityProfileConstraint(Base):
    __tablename__ = "capability_profile_constraint"
    __table_args__ = (UniqueConstraint("profile_id", "code", name="uq_capability_profile_constraint"),)

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(BigIntPK, ForeignKey("capability_profile.id", ondelete="CASCADE"), nullable=False)
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    value_json: Mapped[dict] = mapped_column(JsonType, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    profile: Mapped["CapabilityProfile"] = relationship(back_populates="constraints")


class CapabilityProfileTarget(Base):
    __tablename__ = "capability_profile_target"
    __table_args__ = (UniqueConstraint("profile_id", "target_type", "target_key", name="uq_capability_profile_target"),)

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(BigIntPK, ForeignKey("capability_profile.id", ondelete="CASCADE"), nullable=False)
    target_type: Mapped[str] = mapped_column(String(40), nullable=False)
    target_key: Mapped[str] = mapped_column(String(120), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    metadata_json: Mapped[dict] = mapped_column(JsonType, nullable=False, default=dict, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    profile: Mapped["CapabilityProfile"] = relationship(back_populates="targets")


class CapabilityProfileSnapshot(Base):
    __tablename__ = "capability_profile_snapshot"
    __table_args__ = (UniqueConstraint("profile_id", "snapshot_version", name="uq_capability_profile_snapshot"),)

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(BigIntPK, ForeignKey("capability_profile.id", ondelete="CASCADE"), nullable=False)
    snapshot_version: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot_json: Mapped[dict] = mapped_column(JsonType, nullable=False)
    created_by: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    profile: Mapped["CapabilityProfile"] = relationship(back_populates="snapshots")
