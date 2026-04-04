# 01_source/order_pickup_service/app/models/capability.py
# 04/04/2026 - Capability catalog canônico alinhado ao PostgreSQL

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Index,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


# =========================================================
# Catálogos base
# =========================================================

class CapabilityChannel(Base):
    __tablename__ = "capability_channel"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    contexts: Mapped[list["CapabilityContext"]] = relationship(
        "CapabilityContext",
        back_populates="channel",
        cascade="all, delete-orphan",
    )

    profiles: Mapped[list["CapabilityProfile"]] = relationship(
        "CapabilityProfile",
        back_populates="channel",
    )


class CapabilityContext(Base):
    __tablename__ = "capability_context"
    __table_args__ = (
        UniqueConstraint("channel_id", "code", name="uq_capability_context_channel_code"),
        Index("ix_capability_context_channel", "channel_id"),
        Index("ix_capability_context_active", "is_active"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    channel_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("capability_channel.id", ondelete="RESTRICT"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    channel: Mapped["CapabilityChannel"] = relationship(
        "CapabilityChannel",
        back_populates="contexts",
    )

    profiles: Mapped[list["CapabilityProfile"]] = relationship(
        "CapabilityProfile",
        back_populates="context",
    )


class CapabilityRegion(Base):
    __tablename__ = "capability_region"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    country_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    continent: Mapped[str | None] = mapped_column(String(60), nullable=True)
    default_currency: Mapped[str] = mapped_column(String(10), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    profiles: Mapped[list["CapabilityProfile"]] = relationship(
        "CapabilityProfile",
        back_populates="region",
    )


class PaymentMethodCatalog(Base):
    __tablename__ = "payment_method_catalog"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    family: Mapped[str | None] = mapped_column(String(80), nullable=True)

    is_wallet: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    is_card: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    is_bnpl: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    is_cash_like: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    is_bank_transfer: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")

    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    profile_methods: Mapped[list["CapabilityProfileMethod"]] = relationship(
        "CapabilityProfileMethod",
        back_populates="payment_method",
    )


class PaymentInterfaceCatalog(Base):
    __tablename__ = "payment_interface_catalog"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    interface_type: Mapped[str | None] = mapped_column(String(60), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    profile_method_interfaces: Mapped[list["CapabilityProfileMethodInterface"]] = relationship(
        "CapabilityProfileMethodInterface",
        back_populates="payment_interface",
    )


class WalletProviderCatalog(Base):
    __tablename__ = "wallet_provider_catalog"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    profile_methods: Mapped[list["CapabilityProfileMethod"]] = relationship(
        "CapabilityProfileMethod",
        back_populates="wallet_provider",
    )


class CapabilityRequirementCatalog(Base):
    __tablename__ = "capability_requirement_catalog"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    data_type: Mapped[str] = mapped_column(String(40), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    method_requirements: Mapped[list["CapabilityProfileMethodRequirement"]] = relationship(
        "CapabilityProfileMethodRequirement",
        back_populates="requirement",
    )


# =========================================================
# Profiles
# =========================================================

class CapabilityProfile(Base):
    __tablename__ = "capability_profile"
    __table_args__ = (
        UniqueConstraint(
            "region_id",
            "channel_id",
            "context_id",
            name="uq_capability_profile_region_channel_context",
        ),
        Index("ix_capability_profile_region", "region_id"),
        Index("ix_capability_profile_channel", "channel_id"),
        Index("ix_capability_profile_context", "context_id"),
        Index("ix_capability_profile_active", "is_active"),
        Index("ix_capability_profile_priority", "priority"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    region_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("capability_region.id", ondelete="RESTRICT"),
        nullable=False,
    )
    channel_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("capability_channel.id", ondelete="RESTRICT"),
        nullable=False,
    )
    context_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("capability_context.id", ondelete="RESTRICT"),
        nullable=False,
    )

    profile_code: Mapped[str] = mapped_column(String(160), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100, server_default="100")
    currency: Mapped[str] = mapped_column(String(10), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    region: Mapped["CapabilityRegion"] = relationship(
        "CapabilityRegion",
        back_populates="profiles",
    )
    channel: Mapped["CapabilityChannel"] = relationship(
        "CapabilityChannel",
        back_populates="profiles",
    )
    context: Mapped["CapabilityContext"] = relationship(
        "CapabilityContext",
        back_populates="profiles",
    )

    actions: Mapped[list["CapabilityProfileAction"]] = relationship(
        "CapabilityProfileAction",
        back_populates="profile",
        cascade="all, delete-orphan",
    )
    methods: Mapped[list["CapabilityProfileMethod"]] = relationship(
        "CapabilityProfileMethod",
        back_populates="profile",
        cascade="all, delete-orphan",
    )
    constraints: Mapped[list["CapabilityProfileConstraint"]] = relationship(
        "CapabilityProfileConstraint",
        back_populates="profile",
        cascade="all, delete-orphan",
    )
    targets: Mapped[list["CapabilityProfileTarget"]] = relationship(
        "CapabilityProfileTarget",
        back_populates="profile",
        cascade="all, delete-orphan",
    )
    snapshots: Mapped[list["CapabilityProfileSnapshot"]] = relationship(
        "CapabilityProfileSnapshot",
        back_populates="profile",
        cascade="all, delete-orphan",
    )


class CapabilityProfileAction(Base):
    __tablename__ = "capability_profile_action"
    __table_args__ = (
        UniqueConstraint("profile_id", "action_code", name="uq_capability_profile_action"),
        Index("ix_capability_profile_action_profile", "profile_id"),
        Index("ix_capability_profile_action_active", "is_active"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("capability_profile.id", ondelete="CASCADE"),
        nullable=False,
    )
    action_code: Mapped[str] = mapped_column(String(80), nullable=False)
    label: Mapped[str] = mapped_column(String(120), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=100, server_default="100")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    config_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    profile: Mapped["CapabilityProfile"] = relationship(
        "CapabilityProfile",
        back_populates="actions",
    )


class CapabilityProfileMethod(Base):
    __tablename__ = "capability_profile_method"
    __table_args__ = (
        UniqueConstraint("profile_id", "payment_method_id", name="uq_capability_profile_method"),
        Index("ix_capability_profile_method_profile", "profile_id"),
        Index("ix_capability_profile_method_payment_method", "payment_method_id"),
        Index("ix_capability_profile_method_wallet_provider", "wallet_provider_id"),
        Index("ix_capability_profile_method_active", "is_active"),
        Index(
            "ux_capability_profile_method_default_per_profile",
            "profile_id",
            unique=True,
            postgresql_where=(mapped_column(Boolean).expression if False else None),
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("capability_profile.id", ondelete="CASCADE"),
        nullable=False,
    )
    payment_method_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("payment_method_catalog.id", ondelete="RESTRICT"),
        nullable=False,
    )
    label: Mapped[str | None] = mapped_column(String(120), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=100, server_default="100")
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    wallet_provider_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("wallet_provider_catalog.id", ondelete="RESTRICT"),
        nullable=True,
    )
    rules_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    profile: Mapped["CapabilityProfile"] = relationship(
        "CapabilityProfile",
        back_populates="methods",
    )
    payment_method: Mapped["PaymentMethodCatalog"] = relationship(
        "PaymentMethodCatalog",
        back_populates="profile_methods",
    )
    wallet_provider: Mapped["WalletProviderCatalog | None"] = relationship(
        "WalletProviderCatalog",
        back_populates="profile_methods",
    )

    interfaces: Mapped[list["CapabilityProfileMethodInterface"]] = relationship(
        "CapabilityProfileMethodInterface",
        back_populates="profile_method",
        cascade="all, delete-orphan",
    )
    requirements: Mapped[list["CapabilityProfileMethodRequirement"]] = relationship(
        "CapabilityProfileMethodRequirement",
        back_populates="profile_method",
        cascade="all, delete-orphan",
    )


# índice parcial precisa ser declarado após a classe para usar colunas reais
Index(
    "ux_capability_profile_method_default_per_profile",
    CapabilityProfileMethod.profile_id,
    unique=True,
    postgresql_where=(
        (CapabilityProfileMethod.is_default.is_(True)) &
        (CapabilityProfileMethod.is_active.is_(True))
    ),
)


class CapabilityProfileMethodInterface(Base):
    __tablename__ = "capability_profile_method_interface"
    __table_args__ = (
        UniqueConstraint(
            "profile_method_id",
            "payment_interface_id",
            name="uq_capability_profile_method_interface",
        ),
        Index("ix_capability_profile_method_interface_profile_method", "profile_method_id"),
        Index("ix_capability_profile_method_interface_interface", "payment_interface_id"),
        Index("ix_capability_profile_method_interface_active", "is_active"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    profile_method_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("capability_profile_method.id", ondelete="CASCADE"),
        nullable=False,
    )
    payment_interface_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("payment_interface_catalog.id", ondelete="RESTRICT"),
        nullable=False,
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=100, server_default="100")
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    config_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    profile_method: Mapped["CapabilityProfileMethod"] = relationship(
        "CapabilityProfileMethod",
        back_populates="interfaces",
    )
    payment_interface: Mapped["PaymentInterfaceCatalog"] = relationship(
        "PaymentInterfaceCatalog",
        back_populates="profile_method_interfaces",
    )


Index(
    "ux_cap_profile_method_interface_default",
    CapabilityProfileMethodInterface.profile_method_id,
    unique=True,
    postgresql_where=(
        (CapabilityProfileMethodInterface.is_default.is_(True)) &
        (CapabilityProfileMethodInterface.is_active.is_(True))
    ),
)


class CapabilityProfileMethodRequirement(Base):
    __tablename__ = "capability_profile_method_requirement"
    __table_args__ = (
        UniqueConstraint(
            "profile_method_id",
            "requirement_id",
            name="uq_capability_profile_method_requirement",
        ),
        Index("ix_capability_profile_method_requirement_profile_method", "profile_method_id"),
        Index("ix_capability_profile_method_requirement_requirement", "requirement_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    profile_method_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("capability_profile_method.id", ondelete="CASCADE"),
        nullable=False,
    )
    requirement_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("capability_requirement_catalog.id", ondelete="RESTRICT"),
        nullable=False,
    )
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    requirement_scope: Mapped[str] = mapped_column(String(40), nullable=False, default="request", server_default="request")
    validation_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    profile_method: Mapped["CapabilityProfileMethod"] = relationship(
        "CapabilityProfileMethod",
        back_populates="requirements",
    )
    requirement: Mapped["CapabilityRequirementCatalog"] = relationship(
        "CapabilityRequirementCatalog",
        back_populates="method_requirements",
    )


class CapabilityProfileConstraint(Base):
    __tablename__ = "capability_profile_constraint"
    __table_args__ = (
        UniqueConstraint("profile_id", "code", name="uq_capability_profile_constraint"),
        Index("ix_capability_profile_constraint_profile", "profile_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("capability_profile.id", ondelete="CASCADE"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    value_json: Mapped[dict | str | int | float | bool | list | None] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    profile: Mapped["CapabilityProfile"] = relationship(
        "CapabilityProfile",
        back_populates="constraints",
    )


class CapabilityProfileTarget(Base):
    __tablename__ = "capability_profile_target"
    __table_args__ = (
        UniqueConstraint("profile_id", "target_type", "target_key", name="uq_capability_profile_target"),
        Index("ix_capability_profile_target_profile", "profile_id"),
        Index("ix_capability_profile_target_type_key", "target_type", "target_key"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("capability_profile.id", ondelete="CASCADE"),
        nullable=False,
    )
    target_type: Mapped[str] = mapped_column(String(40), nullable=False)
    target_key: Mapped[str] = mapped_column(String(120), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    profile: Mapped["CapabilityProfile"] = relationship(
        "CapabilityProfile",
        back_populates="targets",
    )


class CapabilityProfileSnapshot(Base):
    __tablename__ = "capability_profile_snapshot"
    __table_args__ = (
        UniqueConstraint("profile_id", "snapshot_version", name="uq_capability_profile_snapshot"),
        Index("ix_capability_profile_snapshot_profile", "profile_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("capability_profile.id", ondelete="CASCADE"),
        nullable=False,
    )
    snapshot_version: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_by: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    profile: Mapped["CapabilityProfile"] = relationship(
        "CapabilityProfile",
        back_populates="snapshots",
    )