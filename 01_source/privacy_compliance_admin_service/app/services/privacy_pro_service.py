from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.privacy import DataSubjectRequest, PrivacyConsent
from app.models.privacy_extended import (
    PrivacyActivityProcessorLink,
    PrivacyBreachIncident,
    PrivacyDataCategory,
    PrivacyProcessingActivity,
    PrivacyProcessor,
)
from app.models.privacy_pro import (
    PrivacyAuditEvent,
    PrivacyBreachTimelineEvent,
    PrivacyDsrTask,
    PrivacyIntegrationHealthCheck,
)
from app.schemas.privacy_pro import (
    AuditEventOut,
    BreachTimelineEventOut,
    BreachTimelineOut,
    ConsentAnalyticsDayOut,
    ConsentAnalyticsOut,
    DsrTaskListOut,
    DsrTaskOut,
    IntegrationHealthListOut,
    IntegrationHealthOut,
    RopaGraphEdgeOut,
    RopaGraphNodeOut,
    RopaGraphOut,
)
from app.services.crypto_util import new_id, utcnow

DSR_PLAYBOOK = [
    ("VERIFY_IDENTITY", 1),
    ("COLLECT_DATA", 2),
    ("REVIEW_LEGAL", 3),
    ("PACKAGE_EXPORT", 4),
    ("NOTIFY_SUBJECT", 5),
]

BREACH_MILESTONES = [
    ("DETECTED", 0),
    ("ASSESSED", 4),
    ("DPO_NOTIFIED", 12),
    ("AUTHORITY_NOTIFIED", 72),
    ("SUBJECTS_NOTIFIED", 72),
    ("CLOSED", None),
]

REGULATORY_DEADLINE_HOURS = {"GDPR": 72, "UKGDPR": 72, "LGPD": 72, "CCPA": 72}


def _aware(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def log_audit(
    db: Session,
    *,
    action: str,
    resource_type: str,
    summary: str,
    resource_id: str | None = None,
    regulation_code: str | None = None,
    actor_id: str | None = "system",
    actor_role: str | None = "admin_operacao",
    payload: dict | None = None,
) -> PrivacyAuditEvent:
    row = PrivacyAuditEvent(
        id=new_id(),
        actor_id=actor_id,
        actor_role=actor_role,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        regulation_code=regulation_code,
        summary=summary,
        payload_json=json.dumps(payload) if payload else None,
        created_at=utcnow(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_audit_events(
    db: Session,
    *,
    regulation_code: str | None = None,
    resource_type: str | None = None,
    limit: int = 100,
) -> list[AuditEventOut]:
    q = db.query(PrivacyAuditEvent)
    if regulation_code:
        q = q.filter(PrivacyAuditEvent.regulation_code == regulation_code.upper())
    if resource_type:
        q = q.filter(PrivacyAuditEvent.resource_type == resource_type)
    rows = q.order_by(PrivacyAuditEvent.created_at.desc()).limit(limit).all()
    return [AuditEventOut.model_validate(r) for r in rows]


def consent_analytics(db: Session, *, regulation_code: str | None = None, days: int = 30) -> ConsentAnalyticsOut:
    since = utcnow() - timedelta(days=days)
    q = db.query(PrivacyConsent).filter(PrivacyConsent.created_at >= since)
    if regulation_code:
        q = q.filter(PrivacyConsent.regulation_code == regulation_code.upper())
    rows = q.all()

    by_channel: dict[str, int] = {}
    by_type: dict[str, int] = {}
    granted = 0
    revoked = 0
    daily_map: dict[str, dict[str, int]] = {}

    for c in rows:
        ch = c.channel or "UNKNOWN"
        by_channel[ch] = by_channel.get(ch, 0) + 1
        by_type[c.consent_type] = by_type.get(c.consent_type, 0) + 1
        if c.revoked_at:
            revoked += 1
        elif c.granted:
            granted += 1
        day = (c.created_at or utcnow()).strftime("%Y-%m-%d")
        if day not in daily_map:
            daily_map[day] = {"granted": 0, "revoked": 0}
        if c.revoked_at:
            daily_map[day]["revoked"] += 1
        elif c.granted:
            daily_map[day]["granted"] += 1

    total = granted + revoked
    opt_out = round(revoked / total * 100, 1) if total else 0.0
    daily = [
        ConsentAnalyticsDayOut(
            date=d,
            granted=v["granted"],
            revoked=v["revoked"],
            net=v["granted"] - v["revoked"],
        )
        for d, v in sorted(daily_map.items())
    ]

    return ConsentAnalyticsOut(
        regulation_code=regulation_code.upper() if regulation_code else None,
        days=days,
        total_granted=granted,
        total_revoked=revoked,
        opt_out_rate_pct=opt_out,
        by_channel=by_channel,
        by_type=by_type,
        daily=daily,
    )


def ensure_breach_timeline(db: Session, breach_id: str) -> PrivacyBreachIncident:
    breach = db.get(PrivacyBreachIncident, breach_id)
    if not breach:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="breach_not_found")
    existing = db.query(PrivacyBreachTimelineEvent).filter_by(breach_id=breach_id).count()
    if existing == 0:
        base = _aware(breach.discovered_at or breach.created_at) or utcnow()
        deadline_h = REGULATORY_DEADLINE_HOURS.get(breach.regulation_code, 72)
        for milestone, offset_h in BREACH_MILESTONES:
            due = None if offset_h is None else base + timedelta(hours=offset_h)
            completed = None
            st = "PENDING"
            if milestone == "DETECTED":
                st = "COMPLETED"
                completed = base
            elif milestone == "AUTHORITY_NOTIFIED" and breach.supervisory_notified_at:
                st = "COMPLETED"
                completed = breach.supervisory_notified_at
            elif milestone == "SUBJECTS_NOTIFIED" and breach.subjects_notified_at:
                st = "COMPLETED"
                completed = breach.subjects_notified_at
            db.add(
                PrivacyBreachTimelineEvent(
                    id=new_id(),
                    breach_id=breach_id,
                    milestone=milestone,
                    status=st,
                    due_at=due if milestone != "CLOSED" else base + timedelta(hours=deadline_h),
                    completed_at=completed,
                    created_at=utcnow(),
                )
            )
        db.commit()
    return breach


def breach_timeline(db: Session, breach_id: str) -> BreachTimelineOut:
    breach = ensure_breach_timeline(db, breach_id)
    items = (
        db.query(PrivacyBreachTimelineEvent)
        .filter_by(breach_id=breach_id)
        .order_by(PrivacyBreachTimelineEvent.created_at)
        .all()
    )
    deadline_h = REGULATORY_DEADLINE_HOURS.get(breach.regulation_code, 72)
    base = _aware(breach.discovered_at or breach.created_at)
    hours_elapsed = None
    on_track = True
    if base:
        hours_elapsed = round((utcnow() - base).total_seconds() / 3600, 1)
        auth = next((i for i in items if i.milestone == "AUTHORITY_NOTIFIED"), None)
        if auth and auth.status != "COMPLETED" and hours_elapsed > deadline_h:
            on_track = False

    return BreachTimelineOut(
        breach_id=breach_id,
        regulation_code=breach.regulation_code,
        items=[BreachTimelineEventOut.model_validate(i) for i in items],
        regulatory_deadline_hours=deadline_h,
        hours_elapsed=hours_elapsed,
        on_track=on_track,
    )


def ensure_dsr_tasks(db: Session, subject_request_id: str) -> DataSubjectRequest:
    req = db.get(DataSubjectRequest, subject_request_id)
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="subject_request_not_found")
    if db.query(PrivacyDsrTask).filter_by(subject_request_id=subject_request_id).count() == 0:
        due_base = req.due_at or (utcnow() + timedelta(days=30))
        for step_code, order in DSR_PLAYBOOK:
            if req.request_type == "ACCESS" and step_code == "PACKAGE_EXPORT":
                pass
            elif req.request_type in ("RECTIFICATION", "RESTRICTION") and step_code == "PACKAGE_EXPORT":
                continue
            db.add(
                PrivacyDsrTask(
                    id=new_id(),
                    subject_request_id=subject_request_id,
                    step_code=step_code,
                    step_order=order,
                    status="COMPLETED" if order == 1 and req.status != "PENDING" else "PENDING",
                    due_at=due_base - timedelta(days=max(0, 30 - order * 5)),
                    created_at=utcnow(),
                )
            )
        db.commit()
    return req


def dsr_tasks(db: Session, subject_request_id: str) -> DsrTaskListOut:
    req = ensure_dsr_tasks(db, subject_request_id)
    items = (
        db.query(PrivacyDsrTask)
        .filter_by(subject_request_id=subject_request_id)
        .order_by(PrivacyDsrTask.step_order)
        .all()
    )
    done = sum(1 for i in items if i.status == "COMPLETED")
    progress = round(done / len(items) * 100, 1) if items else 0.0
    return DsrTaskListOut(
        subject_request_id=subject_request_id,
        request_type=req.request_type,
        regulation_code=req.regulation_code,
        progress_pct=progress,
        items=[DsrTaskOut.model_validate(i) for i in items],
    )


def update_dsr_task(db: Session, task_id: str, *, status: str | None, assignee: str | None, notes: str | None) -> DsrTaskOut:
    row = db.get(PrivacyDsrTask, task_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="dsr_task_not_found")
    if status:
        row.status = status.upper()
        if row.status == "COMPLETED":
            row.completed_at = utcnow()
    if assignee is not None:
        row.assignee = assignee
    if notes is not None:
        row.notes = notes
    db.commit()
    db.refresh(row)
    log_audit(
        db,
        action="DSR_TASK_UPDATE",
        resource_type="privacy_dsr_task",
        resource_id=row.id,
        summary=f"Tarefa DSAR {row.step_code} → {row.status}",
    )
    return DsrTaskOut.model_validate(row)


def ropa_graph(db: Session, regulation_code: str) -> RopaGraphOut:
    code = regulation_code.upper()
    nodes: list[RopaGraphNodeOut] = []
    edges: list[RopaGraphEdgeOut] = []
    activities = db.query(PrivacyProcessingActivity).filter_by(regulation_code=code).all()
    categories = db.query(PrivacyDataCategory).filter_by(regulation_code=code).all()
    processors = db.query(PrivacyProcessor).all()
    proc_by_id = {p.id: p for p in processors}

    for cat in categories:
        nodes.append(RopaGraphNodeOut(id=f"cat-{cat.id}", label=cat.name, node_type="DATA_CATEGORY", regulation_code=code))
    for act in activities:
        nid = f"act-{act.id}"
        nodes.append(RopaGraphNodeOut(id=nid, label=act.name, node_type="PROCESSING_ACTIVITY", regulation_code=code))
        for cat_code in json.loads(act.data_categories_json or "[]"):
            cat = next((c for c in categories if c.code == cat_code), None)
            if cat:
                edges.append(
                    RopaGraphEdgeOut(
                        id=f"e-{act.id}-{cat.id}",
                        source=nid,
                        target=f"cat-{cat.id}",
                        edge_type="PROCESSES",
                    )
                )
    links = db.query(PrivacyActivityProcessorLink).all()
    act_ids = {a.id for a in activities}
    for link in links:
        if link.activity_id not in act_ids:
            continue
        proc = proc_by_id.get(link.processor_id)
        if not proc:
            continue
        pid = f"proc-{proc.id}"
        if not any(n.id == pid for n in nodes):
            nodes.append(RopaGraphNodeOut(id=pid, label=proc.name, node_type="PROCESSOR"))
        edges.append(
            RopaGraphEdgeOut(
                id=f"e-{link.activity_id}-{proc.id}",
                source=f"act-{link.activity_id}",
                target=pid,
                edge_type="SHARES_WITH",
            )
        )
    return RopaGraphOut(regulation_code=code, nodes=nodes, edges=edges)


def list_integration_health(
    db: Session,
    *,
    player_code: str | None = None,
    status_filter: str | None = None,
    limit: int = 200,
) -> IntegrationHealthListOut:
    q = db.query(PrivacyIntegrationHealthCheck)
    if player_code:
        q = q.filter(PrivacyIntegrationHealthCheck.player_code == player_code.upper())
    if status_filter:
        q = q.filter(PrivacyIntegrationHealthCheck.status == status_filter.upper())
    rows = q.order_by(PrivacyIntegrationHealthCheck.checked_at.desc()).limit(limit).all()
    items = [IntegrationHealthOut.model_validate(r) for r in rows]
    healthy = sum(1 for i in items if i.status == "HEALTHY")
    degraded = sum(1 for i in items if i.status == "DEGRADED")
    down = sum(1 for i in items if i.status == "DOWN")
    avg = round(sum(i.score_pct for i in items) / len(items), 1) if items else 0.0
    return IntegrationHealthListOut(
        items=items,
        total=len(items),
        healthy_count=healthy,
        degraded_count=degraded,
        down_count=down,
        avg_score_pct=avg,
    )
