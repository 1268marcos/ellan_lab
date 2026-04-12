# 01_source/order_pickup_service/app/services/payment_capability_service.py

from __future__ import annotations

from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.capability import (
    CapabilityProfile,
    CapabilityProfileAction,
    CapabilityProfileConstraint,
    CapabilityProfileMethod,
    CapabilityProfileMethodInterface,
    CapabilityProfileMethodRequirement,
)


def _serialize_action(action: CapabilityProfileAction) -> dict[str, Any]:
    return {
        "code": action.action_code,
        "label": action.label,
        "sort_order": action.sort_order,
        "config": action.config_json or {},
    }


def _serialize_interface(link: CapabilityProfileMethodInterface) -> dict[str, Any]:
    interface = link.payment_interface
    return {
        "code": interface.code,
        "label": interface.name,
        "type": interface.interface_type,
        "requires_hw": bool(getattr(interface, "requires_hw", False)),
        "default": bool(link.is_default),
        "sort_order": link.sort_order,
        "config": link.config_json or {},
    }


def _serialize_requirement(link: CapabilityProfileMethodRequirement) -> dict[str, Any]:
    requirement = link.requirement
    return {
        "code": requirement.code,
        "name": requirement.name,
        "data_type": requirement.data_type,
        "required": bool(link.is_required),
        "scope": link.requirement_scope,
        "validation": link.validation_json or {},
    }


def _serialize_method(link: CapabilityProfileMethod) -> dict[str, Any]:
    method = link.payment_method
    wallet_provider = link.wallet_provider

    interfaces = sorted(
        [item for item in link.interfaces if item.is_active],
        key=lambda x: (x.sort_order, x.id),
    )
    requirements = sorted(
        list(link.requirements),
        key=lambda x: (x.requirement.code if x.requirement else "", x.id),
    )

    return {
        "method": method.code,
        "label": link.label or method.name,
        "family": method.family,
        "flags": {
            "is_wallet": bool(method.is_wallet),
            "is_card": bool(method.is_card),
            "is_bnpl": bool(method.is_bnpl),
            "is_cash_like": bool(method.is_cash_like),
            "is_bank_transfer": bool(method.is_bank_transfer),
            "is_instant": bool(getattr(method, "is_instant", False)),
        },
        "default": bool(link.is_default),
        "sort_order": link.sort_order,
        "wallet_provider": (
            {
                "code": wallet_provider.code,
                "label": wallet_provider.name,
            }
            if wallet_provider
            else None
        ),
        "rules": link.rules_json or {},
        "interfaces": [_serialize_interface(item) for item in interfaces],
        "requirements": [_serialize_requirement(item) for item in requirements],
    }


def get_payment_capabilities(
    *,
    db: Session,
    region: str,
    channel: str,
    context: str,
) -> dict[str, Any]:
    profile = (
        db.query(CapabilityProfile)
        .options(
            joinedload(CapabilityProfile.region),
            joinedload(CapabilityProfile.channel),
            joinedload(CapabilityProfile.context),
            joinedload(CapabilityProfile.actions),
            joinedload(CapabilityProfile.constraints),
            joinedload(CapabilityProfile.methods)
            .joinedload(CapabilityProfileMethod.payment_method),
            joinedload(CapabilityProfile.methods)
            .joinedload(CapabilityProfileMethod.wallet_provider),
            joinedload(CapabilityProfile.methods)
            .joinedload(CapabilityProfileMethod.interfaces)
            .joinedload(CapabilityProfileMethodInterface.payment_interface),
            joinedload(CapabilityProfile.methods)
            .joinedload(CapabilityProfileMethod.requirements)
            .joinedload(CapabilityProfileMethodRequirement.requirement),
        )
        .join(CapabilityProfile.region)
        .join(CapabilityProfile.channel)
        .join(CapabilityProfile.context)
        .filter(
            CapabilityProfile.is_active.is_(True),
            # CapabilityProfile.region.has(code=region),
            # CapabilityProfile.channel.has(code=channel),
            # CapabilityProfile.context.has(code=context),
            # func.lower(CapabilityProfile.region.has().property.mapper.class_.code) == region.lower(),
            # func.lower(CapabilityProfile.channel.has().property.mapper.class_.code) == channel.lower(),
            # func.lower(CapabilityProfile.context.has().property.mapper.class_.code) == context.lower(),
            func.lower(CapabilityProfile.region.property.mapper.class_.code) == region.lower(),
            func.lower(CapabilityProfile.channel.property.mapper.class_.code) == channel.lower(),
            func.lower(CapabilityProfile.context.property.mapper.class_.code) == context.lower(),
        )
        .order_by(CapabilityProfile.priority.asc(), CapabilityProfile.id.asc())
        .first()
    )

    if profile is None:
        return {
            "found": False,
            "channel": channel,
            "context": context,
            "region": region,
            "message": "Nenhum capability profile ativo encontrado para a combinação informada.",
            "actions": [],
            "methods": [],
            "constraints": {},
        }

    actions = sorted(
        [item for item in profile.actions if item.is_active],
        key=lambda x: (x.sort_order, x.id),
    )

    methods = sorted(
        [item for item in profile.methods if item.is_active],
        key=lambda x: (x.sort_order, x.id),
    )

    constraints = {
        item.code: item.value_json
        for item in profile.constraints
    }

    return {
        "found": True,
        "profile": {
            "id": profile.id,
            "code": profile.profile_code,
            "name": profile.name,
            "priority": profile.priority,
            "active": profile.is_active,
        },
        "channel": profile.channel.code,
        "context": profile.context.code,
        "region": profile.region.code,
        "currency": profile.currency,
        "actions": [_serialize_action(item) for item in actions],
        "methods": [_serialize_method(item) for item in methods],
        "constraints": constraints,
        "metadata": profile.metadata_json or {},
    }