from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.capability import (
    CapabilityChannel,
    CapabilityContext,
    CapabilityProfile,
    CapabilityProfileAction,
    CapabilityProfileConstraint,
    CapabilityProfileMethod,
    CapabilityProfileSnapshot,
    CapabilityRegion,
)
from app.models.ecosystem import CapabilityProfilePlayerBinding
from app.models.ops import CapabilityOpsJob, CapabilityProfileTemplate
from app.services.audit_service import log_audit
from app.services.ecosystem_service import bind_player


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def record_job(
    db: Session,
    job_type: str,
    request: dict,
    result: dict,
    *,
    actor: str | None = None,
    error: str | None = None,
) -> CapabilityOpsJob:
    job = CapabilityOpsJob(
        id=str(uuid.uuid4()),
        job_type=job_type,
        status="FAILED" if error else "COMPLETED",
        actor=actor,
        request_json=request,
        result_json=result,
        error_message=error,
        finished_at=_utcnow(),
    )
    db.add(job)
    return job


def _profile_export_dict(db: Session, profile: CapabilityProfile) -> dict:
    db.refresh(profile)
    actions = db.query(CapabilityProfileAction).filter(CapabilityProfileAction.profile_id == profile.id).all()
    methods = db.query(CapabilityProfileMethod).filter(CapabilityProfileMethod.profile_id == profile.id).all()
    constraints = db.query(CapabilityProfileConstraint).filter(CapabilityProfileConstraint.profile_id == profile.id).all()
    bindings = db.query(CapabilityProfilePlayerBinding).filter(CapabilityProfilePlayerBinding.profile_id == profile.id).all()
    return {
        "profile_code": profile.profile_code,
        "name": profile.name,
        "currency": profile.currency,
        "priority": profile.priority,
        "metadata_json": profile.metadata_json,
        "actions": [
            {"action_code": a.action_code, "label": a.label, "sort_order": a.sort_order, "is_active": a.is_active}
            for a in actions
        ],
        "methods": [
            {
                "payment_method_id": m.payment_method_id,
                "sort_order": m.sort_order,
                "is_default": m.is_default,
                "is_active": m.is_active,
            }
            for m in methods
        ],
        "constraints": [{"code": c.code, "value_json": c.value_json} for c in constraints],
        "bindings": [
            {"player_code": b.player_code, "binding_role": b.binding_role, "priority": b.priority}
            for b in bindings
        ],
    }


def resolve_profile(
    db: Session,
    *,
    region_code: str,
    channel_code: str,
    context_code: str,
    active_only: bool = True,
) -> dict:
    region = db.query(CapabilityRegion).filter(CapabilityRegion.code == region_code).first()
    channel = db.query(CapabilityChannel).filter(CapabilityChannel.code == channel_code).first()
    if not region or not channel:
        raise HTTPException(status_code=404, detail="region_or_channel_not_found")
    ctx = (
        db.query(CapabilityContext)
        .filter(CapabilityContext.channel_id == channel.id, CapabilityContext.code == context_code)
        .first()
    )
    if not ctx:
        raise HTTPException(status_code=404, detail="context_not_found")
    q = db.query(CapabilityProfile).filter(
        CapabilityProfile.region_id == region.id,
        CapabilityProfile.channel_id == channel.id,
        CapabilityProfile.context_id == ctx.id,
    )
    if active_only:
        q = q.filter(CapabilityProfile.is_active.is_(True))
    profile = q.order_by(CapabilityProfile.priority).first()
    if not profile:
        raise HTTPException(status_code=404, detail="profile_not_resolved")
    readiness_gaps: list[str] = []
    if not db.query(CapabilityProfileAction).filter(CapabilityProfileAction.profile_id == profile.id).count():
        readiness_gaps.append("no_actions")
    if not db.query(CapabilityProfileMethod).filter(CapabilityProfileMethod.profile_id == profile.id).count():
        readiness_gaps.append("no_payment_methods")
    return {
        "profile_id": profile.id,
        "profile_code": profile.profile_code,
        "name": profile.name,
        "currency": profile.currency,
        "region_code": region_code,
        "channel_code": channel_code,
        "context_code": context_code,
        "ready_for_checkout": len(readiness_gaps) == 0,
        "gaps": readiness_gaps,
    }


def clone_profile(
    db: Session,
    source_profile_id: int,
    *,
    profile_code: str,
    name: str,
    region_id: int | None = None,
    channel_id: int | None = None,
    context_id: int | None = None,
    copy_bindings: bool = True,
    actor: str | None = None,
) -> CapabilityProfile:
    source = (
        db.query(CapabilityProfile)
        .options(
            joinedload(CapabilityProfile.actions),
            joinedload(CapabilityProfile.methods),
            joinedload(CapabilityProfile.constraints),
        )
        .filter(CapabilityProfile.id == source_profile_id)
        .first()
    )
    if not source:
        raise HTTPException(status_code=404, detail="source_profile_not_found")
    if db.query(CapabilityProfile).filter(CapabilityProfile.profile_code == profile_code).first():
        raise HTTPException(status_code=409, detail="profile_code_exists")
    row = CapabilityProfile(
        region_id=region_id or source.region_id,
        channel_id=channel_id or source.channel_id,
        context_id=context_id or source.context_id,
        profile_code=profile_code,
        name=name,
        currency=source.currency,
        priority=source.priority,
        is_active=False,
        metadata_json={**(source.metadata_json or {}), "cloned_from": source.profile_code},
    )
    db.add(row)
    db.flush()
    for a in source.actions:
        db.add(
            CapabilityProfileAction(
                profile_id=row.id,
                action_code=a.action_code,
                label=a.label,
                sort_order=a.sort_order,
                is_active=a.is_active,
                config_json=a.config_json,
            )
        )
    for m in source.methods:
        db.add(
            CapabilityProfileMethod(
                profile_id=row.id,
                payment_method_id=m.payment_method_id,
                label=m.label,
                sort_order=m.sort_order,
                is_default=m.is_default,
                is_active=m.is_active,
                wallet_provider_id=m.wallet_provider_id,
                rules_json=m.rules_json,
            )
        )
    for c in source.constraints:
        db.add(
            CapabilityProfileConstraint(
                profile_id=row.id,
                code=c.code,
                value_json=c.value_json,
            )
        )
    if copy_bindings:
        for b in db.query(CapabilityProfilePlayerBinding).filter(
            CapabilityProfilePlayerBinding.profile_id == source.id
        ):
            bind_player(
                db,
                profile_id=row.id,
                player_id=b.player_id,
                binding_role=b.binding_role,
                priority=b.priority,
                actor=actor,
            )
    log_audit(
        db,
        entity_type="profile",
        entity_id=str(row.id),
        action="CLONE",
        profile_id=row.id,
        actor=actor,
        payload={"from": source.profile_code, "to": profile_code},
    )
    db.commit()
    db.refresh(row)
    return row


def compare_profiles(db: Session, profile_id_a: int, profile_id_b: int) -> dict:
    a = db.get(CapabilityProfile, profile_id_a)
    b = db.get(CapabilityProfile, profile_id_b)
    if not a or not b:
        raise HTTPException(status_code=404, detail="profile_not_found")
    pa = _profile_export_dict(db, a)
    pb = _profile_export_dict(db, b)
    diff: dict[str, list] = {"only_a": [], "only_b": [], "changed": []}
    for key in ("actions", "methods", "constraints", "bindings"):
        sa = {str(x) for x in pa.get(key, [])}
        sb = {str(x) for x in pb.get(key, [])}
        diff["only_a"].extend([{key: x} for x in pa.get(key, []) if str(x) not in sb])
        diff["only_b"].extend([{key: x} for x in pb.get(key, []) if str(x) not in sa])
    if pa.get("currency") != pb.get("currency"):
        diff["changed"].append({"field": "currency", "a": pa["currency"], "b": pb["currency"]})
    return {"profile_a": a.profile_code, "profile_b": b.profile_code, "diff": diff}


def simulate_flow(db: Session, profile_id: int, flow: str) -> dict:
    profile = db.get(CapabilityProfile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="profile_not_found")
    required_actions = {"pay": ["pay"], "pickup": ["pickup", "pay"], "refund": ["refund"]}.get(flow, [flow])
    codes = {
        a.action_code
        for a in db.query(CapabilityProfileAction).filter(
            CapabilityProfileAction.profile_id == profile_id, CapabilityProfileAction.is_active.is_(True)
        )
    }
    missing = [c for c in required_actions if c not in codes]
    methods = db.query(CapabilityProfileMethod).filter(
        CapabilityProfileMethod.profile_id == profile_id, CapabilityProfileMethod.is_active.is_(True)
    ).count()
    bindings = db.query(CapabilityProfilePlayerBinding).filter(
        CapabilityProfilePlayerBinding.profile_id == profile_id, CapabilityProfilePlayerBinding.is_active.is_(True)
    ).count()
    ok = not missing and methods > 0
    return {
        "flow": flow,
        "profile_code": profile.profile_code,
        "allowed": ok,
        "missing_actions": missing,
        "payment_methods": methods,
        "player_bindings": bindings,
        "hints": [] if ok else ["complete_actions_and_methods"],
    }


def bulk_set_active(db: Session, profile_ids: list[int], is_active: bool, actor: str | None = None) -> dict:
    updated = 0
    for pid in profile_ids:
        row = db.get(CapabilityProfile, pid)
        if not row:
            continue
        row.is_active = is_active
        updated += 1
    log_audit(
        db,
        entity_type="profile",
        entity_id="bulk",
        action="BULK_ACTIVE" if is_active else "BULK_INACTIVE",
        actor=actor,
        payload={"count": updated, "ids": profile_ids},
    )
    db.commit()
    return {"updated": updated}


def export_package(db: Session, profile_id: int) -> dict:
    profile = db.get(CapabilityProfile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="profile_not_found")
    region = db.get(CapabilityRegion, profile.region_id)
    channel = db.get(CapabilityChannel, profile.channel_id)
    ctx = db.get(CapabilityContext, profile.context_id)
    return {
        "version": 1,
        "exported_at": _utcnow().isoformat(),
        "region_code": region.code if region else None,
        "channel_code": channel.code if channel else None,
        "context_code": ctx.code if ctx else None,
        "profile": _profile_export_dict(db, profile),
    }


def list_templates(db: Session) -> list[CapabilityProfileTemplate]:
    return db.query(CapabilityProfileTemplate).filter(CapabilityProfileTemplate.is_active.is_(True)).all()


def create_template_from_profile(
    db: Session, profile_id: int, code: str, name: str, description: str | None = None
) -> CapabilityProfileTemplate:
    profile = db.get(CapabilityProfile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="profile_not_found")
    if db.query(CapabilityProfileTemplate).filter(CapabilityProfileTemplate.code == code).first():
        raise HTTPException(status_code=409, detail="template_code_exists")
    region = db.get(CapabilityRegion, profile.region_id)
    channel = db.get(CapabilityChannel, profile.channel_id)
    ctx = db.get(CapabilityContext, profile.context_id)
    tpl = CapabilityProfileTemplate(
        code=code,
        name=name,
        description=description,
        region_code=region.code if region else None,
        channel_code=channel.code if channel else None,
        context_code=ctx.code if ctx else None,
        currency=profile.currency,
        template_json=_profile_export_dict(db, profile),
    )
    db.add(tpl)
    db.commit()
    db.refresh(tpl)
    return tpl


def apply_template(
    db: Session,
    template_code: str,
    *,
    profile_code: str,
    name: str,
    region_id: int,
    channel_id: int,
    context_id: int,
    actor: str | None = None,
) -> CapabilityProfile:
    tpl = db.query(CapabilityProfileTemplate).filter(CapabilityProfileTemplate.code == template_code).first()
    if not tpl:
        raise HTTPException(status_code=404, detail="template_not_found")
    if db.query(CapabilityProfile).filter(CapabilityProfile.profile_code == profile_code).first():
        raise HTTPException(status_code=409, detail="profile_code_exists")
    body = tpl.template_json or {}
    row = CapabilityProfile(
        region_id=region_id,
        channel_id=channel_id,
        context_id=context_id,
        profile_code=profile_code,
        name=name,
        currency=body.get("currency") or tpl.currency,
        priority=body.get("priority", 100),
        is_active=False,
        metadata_json={"from_template": template_code},
    )
    db.add(row)
    db.flush()
    for a in body.get("actions", []):
        db.add(CapabilityProfileAction(profile_id=row.id, **a))
    for m in body.get("methods", []):
        db.add(CapabilityProfileMethod(profile_id=row.id, **m))
    for c in body.get("constraints", []):
        db.add(CapabilityProfileConstraint(profile_id=row.id, code=c["code"], value_json=c["value_json"]))
    for b in body.get("bindings", []):
        from app.models.ecosystem import CapabilityEcosystemPlayer

        player = db.query(CapabilityEcosystemPlayer).filter(CapabilityEcosystemPlayer.code == b["player_code"]).first()
        if player:
            bind_player(
                db,
                profile_id=row.id,
                player_id=player.id,
                binding_role=b.get("binding_role", "PRIMARY"),
                priority=b.get("priority", 100),
                actor=actor,
            )
    db.commit()
    db.refresh(row)
    return row


def seed_default_templates(db: Session) -> int:
    specs = [
        ("TPL_KIOSK_PURCHASE_BR", "Template kiosk compra BR", "SP", "kiosk", "purchase"),
        ("TPL_KIOSK_PICKUP_BR", "Template kiosk retirada BR", "SP", "kiosk", "pickup"),
        ("TPL_CARRIER_DROPOFF_EU", "Template carrier dropoff EU", "DE", "carrier", "label_dropoff"),
    ]
    count = 0
    for code, tname, reg, ch, ctx_code in specs:
        if db.query(CapabilityProfileTemplate).filter(CapabilityProfileTemplate.code == code).first():
            continue
        region = db.query(CapabilityRegion).filter(CapabilityRegion.code == reg).first()
        channel = db.query(CapabilityChannel).filter(CapabilityChannel.code == ch).first()
        if not region or not channel:
            continue
        ctx = (
            db.query(CapabilityContext)
            .filter(CapabilityContext.channel_id == channel.id, CapabilityContext.code == ctx_code)
            .first()
        )
        if not ctx:
            continue
        profile = (
            db.query(CapabilityProfile)
            .filter(
                CapabilityProfile.region_id == region.id,
                CapabilityProfile.channel_id == channel.id,
                CapabilityProfile.context_id == ctx.id,
            )
            .first()
        )
        if not profile:
            continue
        db.add(
            CapabilityProfileTemplate(
                code=code,
                name=tname,
                region_code=reg,
                channel_code=ch,
                context_code=ctx_code,
                currency=profile.currency,
                template_json=_profile_export_dict(db, profile),
            )
        )
        count += 1
    db.flush()
    return count


def list_jobs(db: Session, limit: int = 50) -> list[CapabilityOpsJob]:
    return db.query(CapabilityOpsJob).order_by(CapabilityOpsJob.created_at.desc()).limit(limit).all()
