from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.security import (
    SecurityAccessReviewCampaign,
    SecurityAccessReviewItem,
    SecurityAlert,
    SecurityAlertRule,
    SecurityApiKey,
    SecurityBreakGlassEvent,
    SecurityComplianceControl,
    SecurityControlMapping,
    SecurityCrossDomainGrant,
    SecurityPermission,
    SecurityPermissionGroup,
    SecurityPermissionMembership,
    SecurityRiskScore,
    SecurityRoleTemplate,
    SecurityUserPlayerAccess,
    SecurityUserSession,
)
from app.models.user import User, UserRole
from app.schemas.security_value import (
    AccessMatrixOut,
    AccessReviewCampaignCreateIn,
    AccessReviewCampaignListOut,
    AccessReviewCampaignOut,
    AccessReviewDecisionIn,
    AccessReviewItemListOut,
    AccessReviewItemOut,
    AlertListOut,
    AlertOut,
    ApplyRoleTemplateIn,
    ApplyRoleTemplateOut,
    BreakGlassCreateIn,
    BreakGlassListOut,
    BreakGlassOut,
    ComplianceControlOut,
    ComplianceListOut,
    RiskScoreListOut,
    RiskScoreOut,
    RoleTemplateListOut,
    RoleTemplateOut,
    SecurityIntelligenceOut,
)
from app.services import user_role_service
from app.services.crypto_util import new_id
from app.schemas.user_role import UserRoleCreateIn
from app.services.security_locker_players_service import create_user_player_access
from app.services.security_professional_service import create_cross_domain_grant
from app.services.security_service import _parse_json, _utcnow, write_audit
from app.schemas.security import CrossDomainGrantCreateIn, UserPlayerAccessCreateIn


def _tier(score: float) -> str:
    if score >= 75:
        return "CRITICAL"
    if score >= 50:
        return "HIGH"
    if score >= 25:
        return "MEDIUM"
    return "LOW"


def compute_risk_scores(db: Session) -> dict[str, int]:
    counts = {"upserted": 0}
    now = _utcnow()

    for user in db.query(User).all():
        factors: list[str] = []
        score = 10.0
        roles = db.query(UserRole).filter(UserRole.user_id == user.id, UserRole.is_active.is_(True), UserRole.revoked_at.is_(None)).count()
        grants = db.query(SecurityCrossDomainGrant).filter(SecurityCrossDomainGrant.user_id == user.id, SecurityCrossDomainGrant.is_active.is_(True)).count()
        players = db.query(SecurityUserPlayerAccess).filter(SecurityUserPlayerAccess.user_id == user.id, SecurityUserPlayerAccess.is_active.is_(True)).count()
        if roles >= 3:
            score += 25
            factors.append("multiple_active_roles")
        if grants >= 5:
            score += 20
            factors.append("broad_cross_domain_grants")
        if players >= 4:
            score += 15
            factors.append("many_locker_networks")
        if user.email and "admin" in user.email:
            score += 10
            factors.append("privileged_email_pattern")
        if not user.is_active:
            score = min(score, 30)
            factors.append("inactive_user")

        _upsert_risk(db, "User", user.id, score, factors, now)
        counts["upserted"] += 1

    for code in ("INPOST", "MERCADOLIVRE", "IFOOD"):
        grant_count = db.query(SecurityCrossDomainGrant).filter(SecurityCrossDomainGrant.entity_id == code).count()
        score = 20 + min(grant_count * 5, 40)
        _upsert_risk(db, "LockerPlayer", code, score, [f"{grant_count}_grants"], now)
        counts["upserted"] += 1

    db.commit()
    return counts


def _upsert_risk(db: Session, etype: str, eid: str, score: float, factors: list[str], now: datetime) -> None:
    tier = _tier(score)
    row = db.query(SecurityRiskScore).filter(SecurityRiskScore.entity_type == etype, SecurityRiskScore.entity_id == eid).first()
    payload = {
        "score": Decimal(str(round(score, 2))),
        "risk_tier": tier,
        "factors_json": json.dumps(factors),
        "computed_at": now,
        "expires_at": now + timedelta(days=7),
    }
    if row:
        for k, v in payload.items():
            setattr(row, k, v)
    else:
        db.add(SecurityRiskScore(id=new_id(), entity_type=etype, entity_id=eid, **payload))


def get_security_intelligence(db: Session) -> SecurityIntelligenceOut:
    compute_risk_scores(db)
    high = db.query(SecurityRiskScore).filter(SecurityRiskScore.risk_tier.in_(["HIGH", "CRITICAL"])).count()
    open_alerts = db.query(SecurityAlert).filter(SecurityAlert.status == "OPEN").count()
    pending = (
        db.query(SecurityAccessReviewItem)
        .filter(SecurityAccessReviewItem.decision.is_(None))
        .count()
    )
    bg = db.query(SecurityBreakGlassEvent).filter(SecurityBreakGlassEvent.status == "ACTIVE").count()
    avg = db.query(func.avg(SecurityRiskScore.score)).scalar() or 0
    total_ctrl = db.query(SecurityComplianceControl).filter(SecurityComplianceControl.is_active.is_(True)).count()
    mapped = db.query(SecurityControlMapping.control_code).distinct().count()
    cov = (mapped / total_ctrl * 100) if total_ctrl else 0

    top = (
        db.query(SecurityRiskScore)
        .order_by(SecurityRiskScore.score.desc())
        .limit(8)
        .all()
    )
    top_risks = [
        {"entity_type": r.entity_type, "entity_id": r.entity_id, "score": float(r.score), "tier": r.risk_tier}
        for r in top
    ]
    recs: list[str] = []
    if open_alerts:
        recs.append(f"Tratar {open_alerts} alerta(s) aberto(s) na fila OPS.")
    if pending:
        recs.append(f"Concluir revisão de acesso: {pending} item(ns) pendente(s).")
    if bg:
        recs.append(f"{bg} sessão(ões) break-glass ativa(s) — validar e revogar após incidente.")
    if cov < 80:
        recs.append("Ampliar mapeamento compliance → permissões (meta 80%+).")
    if not recs:
        recs.append("Postura estável. Agendar próxima campanha de certificação trimestral.")

    posture = "HEALTHY"
    if high >= 3 or open_alerts >= 5:
        posture = "ELEVATED"
    if high >= 8 or bg >= 2:
        posture = "CRITICAL"

    return SecurityIntelligenceOut(
        overall_posture=posture,
        average_user_risk=round(float(avg), 1),
        high_risk_entities=high,
        open_alerts=open_alerts,
        pending_reviews=pending,
        active_break_glass=bg,
        compliance_coverage_pct=round(cov, 1),
        top_risks=top_risks,
        recommendations=recs,
    )


def list_risk_scores(db: Session, tier: str | None = None) -> RiskScoreListOut:
    q = db.query(SecurityRiskScore).order_by(SecurityRiskScore.score.desc())
    if tier:
        q = q.filter(SecurityRiskScore.risk_tier == tier.upper())
    rows = q.limit(100).all()
    items = [
        RiskScoreOut(
            entity_type=r.entity_type,
            entity_id=r.entity_id,
            score=float(r.score),
            risk_tier=r.risk_tier,
            factors=_parse_json(r.factors_json, []),
            computed_at=r.computed_at,
        )
        for r in rows
    ]
    return RiskScoreListOut(items=items, total=len(items))


def list_role_templates(db: Session) -> RoleTemplateListOut:
    rows = db.query(SecurityRoleTemplate).filter(SecurityRoleTemplate.is_active.is_(True)).all()
    items = [
        RoleTemplateOut(
            id=r.id,
            code=r.code,
            name=r.name,
            description=r.description,
            roles=_parse_json(r.roles_json, []),
            permission_groups=_parse_json(r.permission_groups_json, []),
            default_players=_parse_json(r.default_players_json, []),
            target_segment=r.target_segment,
        )
        for r in rows
    ]
    return RoleTemplateListOut(items=items, total=len(items))


def apply_role_template(db: Session, body: ApplyRoleTemplateIn) -> ApplyRoleTemplateOut:
    tpl = db.query(SecurityRoleTemplate).filter(SecurityRoleTemplate.code == body.template_code).first()
    if not tpl:
        raise HTTPException(status_code=404, detail="template_not_found")
    user_role_service.get_user_or_404(db, body.user_id)
    roles_granted = groups_assigned = player_access = 0
    from app.schemas.user_role import UserRoleCreateIn

    for role in _parse_json(tpl.roles_json, []):
        try:
            user_role_service.create_user_role(db, UserRoleCreateIn(user_id=body.user_id, role=role, scope_type="GLOBAL"))
            roles_granted += 1
        except HTTPException as exc:
            if exc.status_code != 409:
                raise
    for gid in _parse_json(tpl.permission_groups_json, []):
        exists = (
            db.query(SecurityPermissionMembership)
            .filter(SecurityPermissionMembership.user_id == body.user_id, SecurityPermissionMembership.group_id == gid)
            .first()
        )
        if not exists:
            db.add(
                SecurityPermissionMembership(
                    id=new_id(),
                    user_id=body.user_id,
                    group_id=gid,
                    is_group_manager=False,
                    created_at=_utcnow(),
                )
            )
            groups_assigned += 1
    for pcode in _parse_json(tpl.default_players_json, []):
        try:
            create_user_player_access(
                db,
                UserPlayerAccessCreateIn(user_id=body.user_id, player_code=pcode, access_role="OPERATOR"),
            )
            player_access += 1
        except HTTPException:
            pass
    write_audit(db, actor_id=body.granted_by, action="ROLE_TEMPLATE_APPLIED", target_type="User", target_id=body.user_id, new_state={"template": body.template_code})
    return ApplyRoleTemplateOut(
        user_id=body.user_id,
        template_code=body.template_code,
        roles_granted=roles_granted,
        groups_assigned=groups_assigned,
        player_access_granted=player_access,
    )


def create_access_review_campaign(db: Session, body: AccessReviewCampaignCreateIn) -> AccessReviewCampaignOut:
    now = _utcnow()
    camp = SecurityAccessReviewCampaign(
        id=new_id(),
        name=body.name,
        status="IN_PROGRESS",
        due_at=body.due_at,
        scope_json=json.dumps(body.scope),
        created_by=body.created_by,
        created_at=now,
    )
    db.add(camp)
    db.flush()
    items = 0
    for grant in db.query(SecurityCrossDomainGrant).filter(SecurityCrossDomainGrant.is_active.is_(True)).all():
        db.add(
            SecurityAccessReviewItem(
                id=new_id(),
                campaign_id=camp.id,
                user_id=grant.user_id,
                subject_type="CrossDomainGrant",
                subject_id=grant.id,
                subject_label=f"{grant.domain_code}/{grant.entity_id}",
                created_at=now,
            )
        )
        items += 1
    for role in db.query(UserRole).filter(UserRole.is_active.is_(True), UserRole.revoked_at.is_(None)).all():
        db.add(
            SecurityAccessReviewItem(
                id=new_id(),
                campaign_id=camp.id,
                user_id=role.user_id,
                subject_type="UserRole",
                subject_id=role.id,
                subject_label=role.role,
                created_at=now,
            )
        )
        items += 1
    db.commit()
    db.refresh(camp)
    return _campaign_out(db, camp)


def _campaign_out(db: Session, camp: SecurityAccessReviewCampaign) -> AccessReviewCampaignOut:
    pending = db.query(SecurityAccessReviewItem).filter(SecurityAccessReviewItem.campaign_id == camp.id, SecurityAccessReviewItem.decision.is_(None)).count()
    approved = db.query(SecurityAccessReviewItem).filter(SecurityAccessReviewItem.campaign_id == camp.id, SecurityAccessReviewItem.decision == "APPROVE").count()
    revoked = db.query(SecurityAccessReviewItem).filter(SecurityAccessReviewItem.campaign_id == camp.id, SecurityAccessReviewItem.decision == "REVOKE").count()
    return AccessReviewCampaignOut(
        id=camp.id,
        name=camp.name,
        status=camp.status,
        due_at=camp.due_at,
        pending_items=pending,
        approved_items=approved,
        revoked_items=revoked,
        created_at=camp.created_at,
    )


def list_campaigns(db: Session) -> AccessReviewCampaignListOut:
    rows = db.query(SecurityAccessReviewCampaign).order_by(SecurityAccessReviewCampaign.created_at.desc()).limit(20).all()
    return AccessReviewCampaignListOut(items=[_campaign_out(db, r) for r in rows], total=len(rows))


def list_review_items(db: Session, campaign_id: str, pending_only: bool = False) -> AccessReviewItemListOut:
    q = db.query(SecurityAccessReviewItem).filter(SecurityAccessReviewItem.campaign_id == campaign_id)
    if pending_only:
        q = q.filter(SecurityAccessReviewItem.decision.is_(None))
    rows = q.limit(500).all()
    return AccessReviewItemListOut(items=[AccessReviewItemOut.model_validate(r) for r in rows], total=len(rows))


def _revoke_cross_domain_grant(db: Session, grant_id: str, *, actor_id: str | None = None) -> None:
    grant = db.get(SecurityCrossDomainGrant, grant_id)
    if not grant or not grant.is_active:
        return
    grant.is_active = False
    write_audit(
        db,
        actor_id=actor_id,
        action="CROSS_DOMAIN_GRANT_REVOKED",
        target_type="CrossDomainGrant",
        target_id=grant.id,
        new_state={"domain": grant.domain_code, "user_id": grant.user_id},
    )


def decide_review_item(db: Session, item_id: str, body: AccessReviewDecisionIn) -> AccessReviewItemOut:
    row = db.get(SecurityAccessReviewItem, item_id)
    if not row:
        raise HTTPException(status_code=404, detail="review_item_not_found")
    if row.decision:
        raise HTTPException(status_code=409, detail="review_item_already_decided")
    row.decision = body.decision
    row.reviewer_id = body.reviewer_id
    row.reviewed_at = _utcnow()
    row.notes = body.notes
    if body.decision == "REVOKE":
        if row.subject_type == "UserRole":
            user_role_service.revoke_user_role(db, row.subject_id)
        elif row.subject_type == "CrossDomainGrant":
            _revoke_cross_domain_grant(db, row.subject_id, actor_id=body.reviewer_id)
    write_audit(
        db,
        actor_id=body.reviewer_id,
        action="ACCESS_REVIEW_DECIDED",
        target_type="AccessReviewItem",
        target_id=row.id,
        new_state={"decision": body.decision, "subject_type": row.subject_type},
    )
    db.commit()
    db.refresh(row)
    return AccessReviewItemOut.model_validate(row)


def _grant_break_glass_roles(db: Session, event_id: str, user_id: str, roles: list[str]) -> None:
    for role_name in roles:
        try:
            user_role_service.create_user_role(
                db,
                UserRoleCreateIn(user_id=user_id, role=role_name, scope_type="BREAK_GLASS", scope_id=event_id),
            )
        except HTTPException as exc:
            if exc.status_code != status.HTTP_409_CONFLICT:
                raise


def _revoke_break_glass_roles(db: Session, event_id: str) -> int:
    rows = (
        db.query(UserRole)
        .filter(
            UserRole.scope_type == "BREAK_GLASS",
            UserRole.scope_id == event_id,
            UserRole.is_active.is_(True),
            UserRole.revoked_at.is_(None),
        )
        .all()
    )
    for row in rows:
        user_role_service.revoke_user_role(db, row.id)
    return len(rows)


def expire_stale_break_glass(db: Session) -> int:
    now = _utcnow()
    expired = 0
    rows = (
        db.query(SecurityBreakGlassEvent)
        .filter(SecurityBreakGlassEvent.status == "ACTIVE", SecurityBreakGlassEvent.expires_at <= now)
        .all()
    )
    for ev in rows:
        _revoke_break_glass_roles(db, ev.id)
        ev.status = "EXPIRED"
        ev.revoked_at = now
        expired += 1
    if expired:
        db.commit()
    return expired


def create_break_glass(db: Session, body: BreakGlassCreateIn) -> BreakGlassOut:
    user_role_service.get_user_or_404(db, body.user_id)
    expire_stale_break_glass(db)
    active = (
        db.query(SecurityBreakGlassEvent)
        .filter(SecurityBreakGlassEvent.user_id == body.user_id, SecurityBreakGlassEvent.status == "ACTIVE")
        .first()
    )
    if active:
        raise HTTPException(status_code=409, detail="break_glass_already_active_for_user")
    now = _utcnow()
    ev = SecurityBreakGlassEvent(
        id=new_id(),
        user_id=body.user_id,
        reason=body.reason,
        granted_roles_json=json.dumps(body.granted_roles),
        approved_by=body.approved_by,
        status="ACTIVE",
        started_at=now,
        expires_at=now + timedelta(hours=body.duration_hours),
    )
    db.add(ev)
    db.flush()
    _grant_break_glass_roles(db, ev.id, body.user_id, body.granted_roles)
    db.commit()
    db.refresh(ev)
    write_audit(db, actor_id=body.approved_by, action="BREAK_GLASS_OPENED", target_type="User", target_id=body.user_id, new_state={"reason": body.reason, "roles": body.granted_roles})
    return BreakGlassOut(
        id=ev.id,
        user_id=ev.user_id,
        reason=ev.reason,
        status=ev.status,
        granted_roles=body.granted_roles,
        started_at=ev.started_at,
        expires_at=ev.expires_at,
    )


def revoke_break_glass(db: Session, event_id: str, *, revoked_by: str | None = None, reason: str | None = None) -> BreakGlassOut:
    ev = db.get(SecurityBreakGlassEvent, event_id)
    if not ev:
        raise HTTPException(status_code=404, detail="break_glass_not_found")
    if ev.status != "ACTIVE":
        raise HTTPException(status_code=409, detail="break_glass_not_active")
    now = _utcnow()
    _revoke_break_glass_roles(db, ev.id)
    ev.status = "REVOKED"
    ev.revoked_at = now
    db.commit()
    db.refresh(ev)
    write_audit(
        db,
        actor_id=revoked_by,
        action="BREAK_GLASS_REVOKED",
        target_type="User",
        target_id=ev.user_id,
        new_state={"event_id": ev.id, "reason": reason},
    )
    return BreakGlassOut(
        id=ev.id,
        user_id=ev.user_id,
        reason=ev.reason,
        status=ev.status,
        granted_roles=_parse_json(ev.granted_roles_json, []),
        started_at=ev.started_at,
        expires_at=ev.expires_at,
    )


def list_break_glass(db: Session, active_only: bool = True) -> BreakGlassListOut:
    try:
        expire_stale_break_glass(db)
    except Exception:
        db.rollback()
    q = db.query(SecurityBreakGlassEvent)
    if active_only:
        q = q.filter(SecurityBreakGlassEvent.status == "ACTIVE")
    rows = q.order_by(SecurityBreakGlassEvent.started_at.desc()).limit(50).all()
    items = [
        BreakGlassOut(
            id=r.id,
            user_id=r.user_id,
            reason=r.reason,
            status=r.status,
            granted_roles=_parse_json(r.granted_roles_json, []),
            started_at=r.started_at,
            expires_at=r.expires_at,
        )
        for r in rows
    ]
    return BreakGlassListOut(items=items, total=len(items))


def list_alerts(db: Session, status: str | None = "OPEN") -> AlertListOut:
    q = db.query(SecurityAlert)
    if status:
        q = q.filter(SecurityAlert.status == status)
    rows = q.order_by(SecurityAlert.created_at.desc()).limit(100).all()
    open_count = db.query(SecurityAlert).filter(SecurityAlert.status == "OPEN").count()
    return AlertListOut(items=[AlertOut.model_validate(r) for r in rows], total=len(rows), open_count=open_count)


def acknowledge_alert(db: Session, alert_id: str, actor_id: str | None) -> AlertOut:
    row = db.get(SecurityAlert, alert_id)
    if not row:
        raise HTTPException(status_code=404, detail="alert_not_found")
    row.status = "ACKNOWLEDGED"
    row.acknowledged_by = actor_id
    row.acknowledged_at = _utcnow()
    db.commit()
    db.refresh(row)
    return AlertOut.model_validate(row)


def list_compliance(db: Session) -> ComplianceListOut:
    rows = db.query(SecurityComplianceControl).filter(SecurityComplianceControl.is_active.is_(True)).order_by(SecurityComplianceControl.framework).all()
    items = []
    for c in rows:
        maps = db.query(SecurityControlMapping).filter(SecurityControlMapping.control_code == c.code).all()
        levels = [m.coverage_level for m in maps]
        cov = levels[0] if len(levels) == 1 else ("FULL" if all(x == "FULL" for x in levels) else "PARTIAL")
        items.append(
            ComplianceControlOut(
                code=c.code,
                framework=c.framework,
                title=c.title,
                description=c.description,
                domain=c.domain,
                mapped_permissions=len(maps),
                coverage_level=cov if maps else None,
            )
        )
    total = len(rows)
    full = sum(1 for i in items if i.mapped_permissions > 0)
    return ComplianceListOut(items=items, total=total, coverage_pct=round(full / total * 100, 1) if total else 0)


def build_access_matrix(db: Session) -> AccessMatrixOut:
    users = [u.id for u in db.query(User).limit(20).all()]
    domains = ["HARDWARE", "MARKETPLACE", "CARRIER", "PARTNER", "ORDER_PICKUP"]
    cells: list[dict[str, Any]] = []
    for g in db.query(SecurityCrossDomainGrant).filter(SecurityCrossDomainGrant.is_active.is_(True)).limit(200).all():
        if g.user_id in users and g.domain_code in domains:
            cells.append({"user_id": g.user_id, "domain": g.domain_code, "level": "grant", "label": g.permission_key})
    return AccessMatrixOut(users=users, domains=domains, cells=cells)


def evaluate_alert_rules(db: Session) -> int:
    created = 0
    rules = {r.code: r for r in db.query(SecurityAlertRule).filter(SecurityAlertRule.is_active.is_(True)).all()}

    if "STALE_API_KEY" in rules:
        stale = db.query(SecurityApiKey).filter(SecurityApiKey.revoked_at.is_(None), SecurityApiKey.last_used_at.is_(None)).count()
        if stale >= 1:
            created += _fire_alert(db, rules["STALE_API_KEY"], "API keys sem uso registrado", f"{stale} chave(s)", "ApiKey", "global")

    if "HIGH_RISK_USER" in rules:
        for r in db.query(SecurityRiskScore).filter(SecurityRiskScore.entity_type == "User", SecurityRiskScore.risk_tier == "CRITICAL").limit(5).all():
            created += _fire_alert(db, rules["HIGH_RISK_USER"], f"Usuário risco crítico: {r.entity_id}", f"score={r.score}", "User", r.entity_id)

    if "BREAK_GLASS_ACTIVE" in rules:
        n = db.query(SecurityBreakGlassEvent).filter(SecurityBreakGlassEvent.status == "ACTIVE").count()
        if n:
            created += _fire_alert(db, rules["BREAK_GLASS_ACTIVE"], "Break-glass ativo", f"{n} sessão(ões)", "Platform", "break-glass")

    db.commit()
    return created


def _fire_alert(db: Session, rule: SecurityAlertRule, title: str, detail: str, etype: str, eid: str) -> int:
    exists = (
        db.query(SecurityAlert)
        .filter(SecurityAlert.rule_id == rule.id, SecurityAlert.status == "OPEN", SecurityAlert.entity_id == eid)
        .first()
    )
    if exists:
        return 0
    db.add(
        SecurityAlert(
            id=new_id(),
            rule_id=rule.id,
            title=title,
            detail=detail,
            entity_type=etype,
            entity_id=eid,
            severity=rule.severity,
            status="OPEN",
            created_at=_utcnow(),
        )
    )
    return 1


def seed_value_layer(db: Session) -> dict[str, int]:
    counts = {"templates": 0, "rules": 0, "compliance": 0, "mappings": 0, "campaign": 0}
    templates = [
        ("tpl-carrier-ops", "Carrier OPS Mundial", "InPost DPD DHL Correios", ["carrier_ops"], ["grp-carriers"], ["INPOST", "DPD", "DHL"], "CARRIER"),
        ("tpl-marketplace-ops", "Marketplace OPS", "Magalu ML Amazon", ["marketplace_seller"], ["grp-marketplace"], ["MAGALU", "MERCADOLIVRE"], "MARKETPLACE"),
        ("tpl-food-delivery", "Food Delivery Integração", "iFood Uber Glovo", ["suporte"], ["grp-ops-read"], ["IFOOD", "UBER_EATS"], "FOOD_DELIVERY"),
        ("tpl-locker-admin", "Locker Network Admin", "Operação rede locker", ["admin_operacao"], ["grp-ops-full"], ["INPOST", "SWIPBOX"], "LOCKER_NETWORK"),
        ("tpl-auditor", "Auditoria Somente Leitura", "Compliance e auditoria", ["auditoria"], ["grp-ops-read"], [], None),
    ]
    for code, name, desc, roles, groups, players, seg in templates:
        if not db.query(SecurityRoleTemplate).filter(SecurityRoleTemplate.code == code).first():
            db.add(
                SecurityRoleTemplate(
                    id=new_id(),
                    code=code,
                    name=name,
                    description=desc,
                    roles_json=json.dumps(roles),
                    permission_groups_json=json.dumps(groups),
                    default_players_json=json.dumps(players),
                    target_segment=seg,
                    is_active=True,
                    created_at=_utcnow(),
                )
            )
            counts["templates"] += 1

    rules = [
        ("STALE_API_KEY", "API key sem uso", "API_KEY_IDLE", {}, "MEDIUM"),
        ("HIGH_RISK_USER", "Usuário risco crítico", "RISK_THRESHOLD", {"min_score": 75}, "HIGH"),
        ("BREAK_GLASS_ACTIVE", "Break-glass ativo", "BREAK_GLASS_COUNT", {"min": 1}, "CRITICAL"),
        ("REVIEW_OVERDUE", "Revisão acesso vencida", "REVIEW_DUE", {}, "MEDIUM"),
    ]
    for code, name, ctype, thresh, sev in rules:
        if not db.query(SecurityAlertRule).filter(SecurityAlertRule.code == code).first():
            db.add(
                SecurityAlertRule(
                    id=new_id(),
                    code=code,
                    name=name,
                    condition_type=ctype,
                    threshold_json=json.dumps(thresh),
                    severity=sev,
                    is_active=True,
                    created_at=_utcnow(),
                )
            )
            counts["rules"] += 1

    controls = [
        ("LGPD-ACCESS-01", "LGPD", "Controle de acesso a dados pessoais", "Identificação e autenticação de usuários OPS", "PARTNER"),
        ("LGPD-AUDIT-02", "LGPD", "Trilha de auditoria", "Registro de ações em audit_logs", "PARTNER"),
        ("GDPR-ART32", "GDPR", "Segurança do tratamento", "Gestão de chaves e webhooks", "PAYMENT_GATEWAY"),
        ("SOC2-CC6.1", "SOC2", "Logical access controls", "RBAC user_roles e permission groups", "PARTNER"),
        ("SOC2-CC6.6", "SOC2", "Credential management", "Rotação API keys", "PARTNER"),
        ("PCI-DSS-7", "PCI-DSS", "Restrict access", "Least privilege cross-domain grants", "PAYMENT_GATEWAY"),
    ]
    for code, fw, title, desc, domain in controls:
        if not db.get(SecurityComplianceControl, code):
            db.add(SecurityComplianceControl(code=code, framework=fw, title=title, description=desc, domain=domain, is_active=True))
            counts["compliance"] += 1

    mappings = [
        ("SOC2-CC6.1", "ops.lockers.read", "FULL"),
        ("SOC2-CC6.1", "ops.lockers.write", "FULL"),
        ("SOC2-CC6.6", "partner.webhook.receive", "PARTIAL"),
        ("LGPD-AUDIT-02", "ops.dashboard.read", "FULL"),
        ("PCI-DSS-7", "marketplace.sellers.manage", "PARTIAL"),
    ]
    for ctrl, obj, level in mappings:
        if not db.query(SecurityControlMapping).filter(SecurityControlMapping.control_code == ctrl, SecurityControlMapping.object_key == obj).first():
            db.add(SecurityControlMapping(id=new_id(), control_code=ctrl, object_key=obj, coverage_level=level))
            counts["mappings"] += 1

    if not db.query(SecurityAccessReviewCampaign).filter(SecurityAccessReviewCampaign.name == "Q2-2026 Certificação Mundial").first():
        due = _utcnow() + timedelta(days=30)
        create_access_review_campaign(
            db,
            AccessReviewCampaignCreateIn(name="Q2-2026 Certificação Mundial", due_at=due, created_by="usr-admin-ops"),
        )
        counts["campaign"] = 1

    compute_risk_scores(db)
    counts["alerts_fired"] = evaluate_alert_rules(db)
    db.commit()
    from app.services.security_cross_ops_service import seed_cross_ops

    counts["cross_ops"] = seed_cross_ops(db)
    return counts
