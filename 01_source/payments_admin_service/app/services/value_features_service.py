from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.cross_domain import (
    PaymentEcosystemPlayer,
    PaymentPlayerIntegration,
    PaymentPlayerRelation,
)
from app.models.value_features import (
    PaymentIntegrationIncident,
    PaymentIntegrationMilestone,
    PaymentPlayerCompliance,
    PaymentRoutingRule,
    PaymentSettlementCorridor,
)
from app.schemas.value_features import (
    EcosystemGraphEdge,
    EcosystemGraphNode,
    EcosystemGraphOut,
    GlobalReadinessOut,
    IntegrationMilestoneIn,
    IntegrationMilestoneUpdate,
    RoutingRuleIn,
    RoutingRuleUpdate,
    RoutingSuggestionOut,
)
from app.services.crypto_util import new_id


def get_milestone(db: Session, milestone_id: str) -> PaymentIntegrationMilestone | None:
    return db.get(PaymentIntegrationMilestone, milestone_id)


def create_milestone(db: Session, body: IntegrationMilestoneIn) -> PaymentIntegrationMilestone:
    row = PaymentIntegrationMilestone(
        id=new_id(),
        player_code=body.player_code.upper(),
        phase=body.phase.upper(),
        title=body.title,
        status=body.status.upper(),
        target_date=body.target_date,
        owner_team=body.owner_team,
        blockers_json=body.blockers_json,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_milestone(
    db: Session, milestone_id: str, body: IntegrationMilestoneUpdate
) -> PaymentIntegrationMilestone | None:
    row = db.get(PaymentIntegrationMilestone, milestone_id)
    if not row:
        return None
    data = body.model_dump(exclude_unset=True)
    if "phase" in data and data["phase"]:
        data["phase"] = data["phase"].upper()
    if "status" in data and data["status"]:
        data["status"] = data["status"].upper()
    for k, v in data.items():
        setattr(row, k, v)
    if data.get("status") == "DONE" and not row.completed_at:
        from datetime import datetime, timezone

        row.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(row)
    return row


def delete_milestone(db: Session, milestone_id: str) -> bool:
    row = db.get(PaymentIntegrationMilestone, milestone_id)
    if not row:
        return False
    db.delete(row)
    db.commit()
    return True


def get_routing_rule(db: Session, rule_id: str) -> PaymentRoutingRule | None:
    return db.get(PaymentRoutingRule, rule_id)


def create_routing_rule(db: Session, body: RoutingRuleIn) -> PaymentRoutingRule:
    row = PaymentRoutingRule(
        id=new_id(),
        rule_code=body.rule_code.upper(),
        tenant_id=body.tenant_id,
        country_code=body.country_code.upper(),
        payment_method=body.payment_method.upper(),
        sales_channel=body.sales_channel.upper() if body.sales_channel else None,
        primary_player_code=body.primary_player_code.upper(),
        fallback_player_code=body.fallback_player_code.upper() if body.fallback_player_code else None,
        priority=body.priority,
        min_amount_cents=body.min_amount_cents,
        max_amount_cents=body.max_amount_cents,
        is_active=body.is_active,
        rationale=body.rationale,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_routing_rule(
    db: Session, rule_id: str, body: RoutingRuleUpdate
) -> PaymentRoutingRule | None:
    row = db.get(PaymentRoutingRule, rule_id)
    if not row:
        return None
    data = body.model_dump(exclude_unset=True)
    for key in ("country_code", "payment_method", "primary_player_code", "sales_channel"):
        if key in data and data[key]:
            data[key] = data[key].upper()
    if "fallback_player_code" in data and data["fallback_player_code"]:
        data["fallback_player_code"] = data["fallback_player_code"].upper()
    for k, v in data.items():
        setattr(row, k, v)
    db.commit()
    db.refresh(row)
    return row


def delete_routing_rule(db: Session, rule_id: str) -> bool:
    row = db.get(PaymentRoutingRule, rule_id)
    if not row:
        return False
    db.delete(row)
    db.commit()
    return True


def list_milestones(
    db: Session,
    *,
    player_code: str | None = None,
    status: str | None = None,
    limit: int = 200,
) -> list[PaymentIntegrationMilestone]:
    q = db.query(PaymentIntegrationMilestone)
    if player_code:
        q = q.filter(PaymentIntegrationMilestone.player_code == player_code.upper())
    if status:
        q = q.filter(PaymentIntegrationMilestone.status == status.upper())
    return q.order_by(PaymentIntegrationMilestone.player_code, PaymentIntegrationMilestone.phase).limit(limit).all()


def list_corridors(
    db: Session,
    *,
    origin_country: str | None = None,
    active_only: bool = True,
    limit: int = 100,
) -> list[PaymentSettlementCorridor]:
    q = db.query(PaymentSettlementCorridor)
    if origin_country:
        q = q.filter(PaymentSettlementCorridor.origin_country == origin_country.upper())
    if active_only:
        q = q.filter(PaymentSettlementCorridor.is_active.is_(True))
    return q.order_by(PaymentSettlementCorridor.corridor_code).limit(limit).all()


def list_compliance(
    db: Session,
    *,
    player_code: str | None = None,
    country_code: str | None = None,
    limit: int = 200,
) -> list[PaymentPlayerCompliance]:
    q = db.query(PaymentPlayerCompliance)
    if player_code:
        q = q.filter(PaymentPlayerCompliance.player_code == player_code.upper())
    if country_code:
        q = q.filter(PaymentPlayerCompliance.country_code == country_code.upper())
    return q.order_by(PaymentPlayerCompliance.risk_tier.desc()).limit(limit).all()


def list_routing_rules(
    db: Session,
    *,
    country_code: str | None = None,
    payment_method: str | None = None,
    active_only: bool = True,
    limit: int = 100,
) -> list[PaymentRoutingRule]:
    q = db.query(PaymentRoutingRule)
    if country_code:
        q = q.filter(PaymentRoutingRule.country_code == country_code.upper())
    if payment_method:
        q = q.filter(PaymentRoutingRule.payment_method == payment_method.upper())
    if active_only:
        q = q.filter(PaymentRoutingRule.is_active.is_(True))
    return q.order_by(PaymentRoutingRule.priority).limit(limit).all()


def list_incidents(
    db: Session,
    *,
    status: str | None = None,
    player_code: str | None = None,
    limit: int = 100,
) -> list[PaymentIntegrationIncident]:
    q = db.query(PaymentIntegrationIncident)
    if status:
        q = q.filter(PaymentIntegrationIncident.status == status.upper())
    if player_code:
        q = q.filter(PaymentIntegrationIncident.player_code == player_code.upper())
    return q.order_by(PaymentIntegrationIncident.started_at.desc()).limit(limit).all()


def build_ecosystem_graph(db: Session, *, limit_nodes: int = 120) -> EcosystemGraphOut:
    players = (
        db.query(PaymentEcosystemPlayer)
        .filter(PaymentEcosystemPlayer.is_active.is_(True))
        .limit(limit_nodes)
        .all()
    )
    codes = {p.code for p in players}
    integ_map = {
        i.player_code: i.readiness_score
        for i in db.query(PaymentPlayerIntegration)
        .filter(PaymentPlayerIntegration.player_code.in_(codes))
        .all()
    }
    nodes = [
        EcosystemGraphNode(
            id=p.id,
            code=p.code,
            label=p.name,
            segment=p.segment,
            integration_status=p.integration_status,
            readiness_score=integ_map.get(p.code),
        )
        for p in players
    ]
    rels = (
        db.query(PaymentPlayerRelation)
        .filter(
            PaymentPlayerRelation.is_active.is_(True),
            PaymentPlayerRelation.from_player_code.in_(codes),
            PaymentPlayerRelation.to_player_code.in_(codes),
        )
        .limit(200)
        .all()
    )
    edges = [
        EcosystemGraphEdge(
            from_code=r.from_player_code,
            to_code=r.to_player_code,
            relation_type=r.relation_type,
        )
        for r in rels
    ]
    return EcosystemGraphOut(
        nodes=nodes,
        edges=edges,
        node_count=len(nodes),
        edge_count=len(edges),
    )


def suggest_routing(
    db: Session,
    *,
    country_code: str,
    payment_method: str,
    amount_cents: int | None = None,
    sales_channel: str | None = None,
) -> RoutingSuggestionOut | None:
    country = country_code.upper()
    method = payment_method.upper()
    q = (
        db.query(PaymentRoutingRule)
        .filter(
            PaymentRoutingRule.is_active.is_(True),
            PaymentRoutingRule.payment_method == method,
        )
        .filter(
            (PaymentRoutingRule.country_code == country) | (PaymentRoutingRule.country_code == "XX")
        )
    )
    if sales_channel:
        q = q.filter(
            (PaymentRoutingRule.sales_channel == sales_channel.upper())
            | (PaymentRoutingRule.sales_channel.is_(None))
        )
    rules = q.order_by(PaymentRoutingRule.priority).all()
    for rule in rules:
        if rule.min_amount_cents is not None and amount_cents is not None:
            if amount_cents < rule.min_amount_cents:
                continue
        if rule.max_amount_cents is not None and amount_cents is not None:
            if amount_cents > rule.max_amount_cents:
                continue
        integ = (
            db.query(PaymentPlayerIntegration)
            .filter(PaymentPlayerIntegration.player_code == rule.primary_player_code)
            .first()
        )
        return RoutingSuggestionOut(
            country_code=country,
            payment_method=method,
            amount_cents=amount_cents,
            primary_player_code=rule.primary_player_code,
            fallback_player_code=rule.fallback_player_code,
            rule_code=rule.rule_code,
            rationale=rule.rationale,
            readiness_score=integ.readiness_score if integ else None,
        )
    return None


def build_global_readiness(db: Session) -> GlobalReadinessOut:
    players_total = (
        db.query(PaymentEcosystemPlayer).filter(PaymentEcosystemPlayer.is_active.is_(True)).count()
    )
    prod = (
        db.query(PaymentPlayerIntegration)
        .filter(PaymentPlayerIntegration.production_ready.is_(True))
        .count()
    )
    avg = db.query(func.avg(PaymentPlayerIntegration.readiness_score)).scalar() or 0.0
    open_inc = (
        db.query(PaymentIntegrationIncident)
        .filter(PaymentIntegrationIncident.status == "OPEN")
        .count()
    )
    crit = (
        db.query(PaymentIntegrationIncident)
        .filter(
            PaymentIntegrationIncident.status == "OPEN",
            PaymentIntegrationIncident.severity == "CRITICAL",
        )
        .count()
    )
    mip = (
        db.query(PaymentIntegrationMilestone)
        .filter(PaymentIntegrationMilestone.status == "IN_PROGRESS")
        .count()
    )
    blocked = (
        db.query(PaymentIntegrationMilestone)
        .filter(PaymentIntegrationMilestone.status == "BLOCKED")
        .count()
    )
    corridors = (
        db.query(PaymentSettlementCorridor)
        .filter(PaymentSettlementCorridor.is_active.is_(True))
        .count()
    )
    approved = (
        db.query(PaymentPlayerCompliance)
        .filter(PaymentPlayerCompliance.audit_status == "APPROVED")
        .count()
    )
    rules = db.query(PaymentRoutingRule).filter(PaymentRoutingRule.is_active.is_(True)).count()
    top_risk = [
        r[0]
        for r in (
            db.query(PaymentPlayerCompliance.player_code)
            .filter(PaymentPlayerCompliance.risk_tier == "HIGH")
            .limit(8)
            .all()
        )
    ]
    return GlobalReadinessOut(
        players_total=players_total,
        production_integrations=prod,
        avg_readiness=round(float(avg), 1),
        open_incidents=open_inc,
        critical_incidents=crit,
        milestones_in_progress=mip,
        milestones_blocked=blocked,
        active_corridors=corridors,
        compliance_approved=approved,
        active_routing_rules=rules,
        top_risk_players=top_risk,
    )
