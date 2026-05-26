from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.data.ops_intelligence_seed import CROSS_BORDER_DEMO, OPS_PLAYBOOKS, PROMO_DEMO
from app.models.marketplace_extended import MarketplaceChannelPartner
from app.models.marketplace_integration import MarketplaceIntegrationReadiness
from app.models.marketplace_ops_intelligence import (
    MarketplaceOpsPlaybook,
    MarketplacePartnerApiHealth,
    SellerCatalogSyncJob,
    SellerChannelQuota,
    SellerCrossBorderProfile,
    SellerHealthSnapshot,
    SellerPromotionCampaign,
)
from app.models.seller_professional import SellerRiskAssessment
from app.schemas.marketplace_ops_intelligence import (
    CatalogSyncJobCreateIn,
    CrossBorderProfileCreateIn,
    PromotionCampaignCreateIn,
)
from app.services.crypto_util import new_id
from app.services.seller_player_coverage_service import seller_player_coverage
from app.services.seller_service import get_seller_or_404


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _band(score: float) -> str:
    if score >= 85:
        return "GREEN"
    if score >= 65:
        return "YELLOW"
    return "RED"


def seed_ops_intelligence(db: Session) -> dict[str, int]:
    counts = {
        "playbooks": 0,
        "quotas": 0,
        "cross_border": 0,
        "api_health": 0,
        "promotions": 0,
        "health_snapshots": 0,
        "sync_jobs": 0,
    }
    for spec in OPS_PLAYBOOKS:
        if db.get(MarketplaceOpsPlaybook, spec["id"]):
            continue
        db.add(
            MarketplaceOpsPlaybook(
                id=spec["id"],
                code=spec["code"],
                name=spec["name"],
                trigger_type=spec["trigger_type"],
                severity=spec["severity"],
                steps_json=json.dumps(spec["steps"]),
                owner_team=spec.get("owner_team"),
            )
        )
        counts["playbooks"] += 1

    quota_channels = [
        ("mk-quota-meli", "mk-seller-demo-001", "mcp-meli", 5000, 800, 30, 120, 45),
        ("mk-quota-magalu", "mk-seller-demo-001", "mcp-magalu", 3000, 500, 20, 85, 12),
        ("mk-quota-amazon", "mk-seller-demo-001", "mcp-amazon-br", 8000, 1200, 40, 200, 88),
    ]
    for qid, sid, pid, max_sku, max_ord, max_locker, cur_sku, cur_ord in quota_channels:
        if not db.get(MarketplaceChannelPartner, pid):
            continue
        if db.get(SellerChannelQuota, qid):
            continue
        util_sku = 100.0 * cur_sku / max_sku if max_sku else 0
        util_ord = 100.0 * cur_ord / max_ord if max_ord else 0
        status_q = "OK"
        if util_sku >= 95 or util_ord >= 95:
            status_q = "CRITICAL"
        elif util_sku >= 80 or util_ord >= 80:
            status_q = "WARNING"
        db.add(
            SellerChannelQuota(
                id=qid,
                seller_id=sid,
                channel_partner_id=pid,
                max_active_skus=max_sku,
                max_orders_per_day=max_ord,
                max_lockers_linked=max_locker,
                current_skus=cur_sku,
                current_orders_today=cur_ord,
                quota_status=status_q,
            )
        )
        counts["quotas"] += 1

    for xid, sid, corridor, scheme, orig, dest, ioss, vat, eori, st in CROSS_BORDER_DEMO:
        if db.get(SellerCrossBorderProfile, xid):
            continue
        verified = _utcnow() if st == "VERIFIED" else None
        db.add(
            SellerCrossBorderProfile(
                id=xid,
                seller_id=sid,
                corridor_code=corridor,
                customs_scheme=scheme,
                origin_country=orig,
                dest_country=dest,
                ioss_number=ioss,
                vat_number=vat,
                eori_number=eori,
                status=st,
                verified_at=verified,
            )
        )
        counts["cross_border"] += 1

    now = _utcnow()
    for partner in db.query(MarketplaceChannelPartner).filter(MarketplaceChannelPartner.active.is_(True)).limit(25).all():
        hid = f"mk-apih-{partner.code.lower()[:20]}"
        if db.get(MarketplacePartnerApiHealth, hid):
            continue
        score = float(
            db.query(MarketplaceIntegrationReadiness.score_total)
            .filter(MarketplaceIntegrationReadiness.partner_code == partner.code)
            .scalar()
            or 70
        )
        avail = min(100.0, score + 10)
        err = max(0.0, 100.0 - score) / 10
        lat = int(500 + (100 - score) * 30)
        hst = "HEALTHY" if avail >= 98 else "DEGRADED" if avail >= 90 else "OUTAGE"
        db.add(
            MarketplacePartnerApiHealth(
                id=hid,
                channel_partner_id=partner.id,
                partner_code=partner.code,
                measured_at=now,
                availability_pct=Decimal(str(round(avail, 2))),
                p95_latency_ms=lat,
                error_rate_pct=Decimal(str(round(err, 2))),
                rate_limit_hits=2 if hst != "HEALTHY" else 0,
                health_status=hst,
            )
        )
        counts["api_health"] += 1

    for pid, sid, cpid, code, name, disc, st in PROMO_DEMO:
        if not db.get(MarketplaceChannelPartner, cpid):
            continue
        if db.get(SellerPromotionCampaign, pid):
            continue
        db.add(
            SellerPromotionCampaign(
                id=pid,
                seller_id=sid,
                channel_partner_id=cpid,
                campaign_code=code,
                name=name,
                discount_pct=Decimal(str(disc)),
                starts_at=now,
                ends_at=now + timedelta(days=30),
                status=st,
                budget_cents=500_000,
                spent_cents=120_000 if st == "ACTIVE" else 0,
            )
        )
        counts["promotions"] += 1

    compute_seller_health(db, "mk-seller-demo-001")
    counts["health_snapshots"] += 1

    if not db.get(SellerCatalogSyncJob, "mk-sync-meli-demo"):
        db.add(
            SellerCatalogSyncJob(
                id="mk-sync-meli-demo",
                seller_id="mk-seller-demo-001",
                channel_partner_id="mcp-meli",
                job_type="FULL_CATALOG_PUSH",
                status="COMPLETED",
                items_total=120,
                items_ok=118,
                items_failed=2,
                started_at=now - timedelta(hours=2),
                finished_at=now - timedelta(hours=1, minutes=50),
            )
        )
        counts["sync_jobs"] += 1

    db.commit()
    return counts


def compute_seller_health(db: Session, seller_id: str) -> SellerHealthSnapshot:
    get_seller_or_404(db, seller_id)
    today = date.today()
    existing = (
        db.query(SellerHealthSnapshot)
        .filter(SellerHealthSnapshot.seller_id == seller_id, SellerHealthSnapshot.snapshot_date == today)
        .first()
    )
    cov = seller_player_coverage(db, seller_id)
    coverage_pct = float(cov.get("coverage_pct", 0))
    readiness_rows = db.query(MarketplaceIntegrationReadiness).all()
    readiness_avg = (
        sum(float(r.score_total) for r in readiness_rows) / len(readiness_rows) if readiness_rows else 50.0
    )
    risk = (
        db.query(SellerRiskAssessment)
        .filter(SellerRiskAssessment.seller_id == seller_id)
        .order_by(SellerRiskAssessment.assessed_at.desc())
        .first()
    )
    risk_level = risk.risk_band if risk else "LOW"
    open_incidents = 0
    factors: list[str] = []
    if coverage_pct < 70:
        factors.append("low_player_coverage")
    if readiness_avg < 60:
        factors.append("low_integration_readiness")
    if risk_level in ("HIGH", "CRITICAL"):
        factors.append("elevated_risk")
    quotas_warn = (
        db.query(SellerChannelQuota)
        .filter(SellerChannelQuota.seller_id == seller_id, SellerChannelQuota.quota_status != "OK")
        .count()
    )
    if quotas_warn:
        factors.append("quota_pressure")
    score = min(
        100.0,
        max(
            0.0,
            0.45 * coverage_pct + 0.35 * readiness_avg + 0.20 * (100 if risk_level == "LOW" else 60 if risk_level == "MEDIUM" else 30),
        ),
    )
    band = _band(score)
    payload = dict(
        seller_id=seller_id,
        snapshot_date=today,
        health_score=Decimal(str(round(score, 2))),
        health_band=band,
        coverage_pct=Decimal(str(round(coverage_pct, 2))),
        readiness_avg=Decimal(str(round(readiness_avg, 2))),
        open_incidents=open_incidents,
        kyc_status="APPROVED",
        risk_level=risk_level,
        factors_json=json.dumps(factors),
    )
    if existing:
        for k, v in payload.items():
            setattr(existing, k, v)
        row = existing
    else:
        row = SellerHealthSnapshot(id=new_id(), **payload)
        db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_summary(db: Session) -> dict:
    return {
        "playbooks_total": db.query(MarketplaceOpsPlaybook).filter(MarketplaceOpsPlaybook.active.is_(True)).count(),
        "api_health_degraded": db.query(MarketplacePartnerApiHealth)
        .filter(MarketplacePartnerApiHealth.health_status != "HEALTHY")
        .count(),
        "sellers_with_health": db.query(func.count(func.distinct(SellerHealthSnapshot.seller_id))).scalar() or 0,
        "active_promotions": db.query(SellerPromotionCampaign)
        .filter(SellerPromotionCampaign.status == "ACTIVE")
        .count(),
        "sync_jobs_running": db.query(SellerCatalogSyncJob).filter(SellerCatalogSyncJob.status.in_(("QUEUED", "RUNNING"))).count(),
        "cross_border_profiles": db.query(SellerCrossBorderProfile).count(),
    }


def list_playbooks(db: Session, trigger_type: str | None = None) -> list[MarketplaceOpsPlaybook]:
    q = db.query(MarketplaceOpsPlaybook).filter(MarketplaceOpsPlaybook.active.is_(True))
    if trigger_type:
        q = q.filter(MarketplaceOpsPlaybook.trigger_type == trigger_type)
    return q.order_by(MarketplaceOpsPlaybook.severity.desc()).all()


def playbook_out(row: MarketplaceOpsPlaybook) -> dict:
    try:
        steps = json.loads(row.steps_json or "[]")
    except json.JSONDecodeError:
        steps = []
    return {**{c.name: getattr(row, c.name) for c in row.__table__.columns}, "steps": steps}


def list_health(db: Session, seller_id: str, limit: int = 30) -> list[SellerHealthSnapshot]:
    get_seller_or_404(db, seller_id)
    return (
        db.query(SellerHealthSnapshot)
        .filter(SellerHealthSnapshot.seller_id == seller_id)
        .order_by(SellerHealthSnapshot.snapshot_date.desc())
        .limit(limit)
        .all()
    )


def health_out(row: SellerHealthSnapshot) -> dict:
    try:
        factors = json.loads(row.factors_json or "[]")
    except json.JSONDecodeError:
        factors = []
    return {**{c.name: getattr(row, c.name) for c in row.__table__.columns}, "factors": factors}


def list_quotas(db: Session, seller_id: str) -> list[dict]:
    get_seller_or_404(db, seller_id)
    codes = {p.id: p.code for p in db.query(MarketplaceChannelPartner).all()}
    out = []
    for q in db.query(SellerChannelQuota).filter(SellerChannelQuota.seller_id == seller_id).all():
        util_sku = 100.0 * q.current_skus / q.max_active_skus if q.max_active_skus else 0
        util_ord = 100.0 * q.current_orders_today / q.max_orders_per_day if q.max_orders_per_day else 0
        out.append(
            {
                **{c.name: getattr(q, c.name) for c in q.__table__.columns},
                "partner_code": codes.get(q.channel_partner_id),
                "utilization_skus_pct": round(util_sku, 1),
                "utilization_orders_pct": round(util_ord, 1),
            }
        )
    return out


def create_sync_job(db: Session, body: CatalogSyncJobCreateIn) -> SellerCatalogSyncJob:
    get_seller_or_404(db, body.seller_id)
    if not db.get(MarketplaceChannelPartner, body.channel_partner_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="channel_partner_not_found")
    row = SellerCatalogSyncJob(
        id=new_id(),
        seller_id=body.seller_id,
        channel_partner_id=body.channel_partner_id,
        job_type=body.job_type,
        status="QUEUED",
        items_total=body.items_total,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def run_sync_job(db: Session, job_id: str) -> SellerCatalogSyncJob:
    row = db.get(SellerCatalogSyncJob, job_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="sync_job_not_found")
    now = _utcnow()
    row.status = "RUNNING"
    row.started_at = now
    total = row.items_total or 100
    row.items_total = total
    row.items_ok = int(total * 0.97)
    row.items_failed = total - row.items_ok
    row.status = "COMPLETED" if row.items_failed < 5 else "PARTIAL"
    row.finished_at = now + timedelta(seconds=30)
    db.commit()
    db.refresh(row)
    return row


def list_sync_jobs(db: Session, seller_id: str | None = None, status_filter: str | None = None) -> list[dict]:
    q = db.query(SellerCatalogSyncJob)
    if seller_id:
        q = q.filter(SellerCatalogSyncJob.seller_id == seller_id)
    if status_filter:
        q = q.filter(SellerCatalogSyncJob.status == status_filter)
    codes = {p.id: p.code for p in db.query(MarketplaceChannelPartner).all()}
    rows = q.order_by(SellerCatalogSyncJob.created_at.desc()).limit(50).all()
    return [{**{c.name: getattr(r, c.name) for c in r.__table__.columns}, "partner_code": codes.get(r.channel_partner_id)} for r in rows]


def sync_job_out(row: SellerCatalogSyncJob, partner_code: str | None = None) -> dict:
    return {**{c.name: getattr(row, c.name) for c in row.__table__.columns}, "partner_code": partner_code}


def create_cross_border(db: Session, body: CrossBorderProfileCreateIn) -> SellerCrossBorderProfile:
    get_seller_or_404(db, body.seller_id)
    exists = (
        db.query(SellerCrossBorderProfile)
        .filter(
            SellerCrossBorderProfile.seller_id == body.seller_id,
            SellerCrossBorderProfile.corridor_code == body.corridor_code,
        )
        .first()
    )
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="cross_border_exists")
    row = SellerCrossBorderProfile(id=new_id(), **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_cross_border(db: Session, seller_id: str) -> list[SellerCrossBorderProfile]:
    get_seller_or_404(db, seller_id)
    return (
        db.query(SellerCrossBorderProfile)
        .filter(SellerCrossBorderProfile.seller_id == seller_id)
        .order_by(SellerCrossBorderProfile.corridor_code)
        .all()
    )


def list_api_health(db: Session, degraded_only: bool = False, limit: int = 50) -> list[MarketplacePartnerApiHealth]:
    q = db.query(MarketplacePartnerApiHealth)
    if degraded_only:
        q = q.filter(MarketplacePartnerApiHealth.health_status != "HEALTHY")
    return q.order_by(MarketplacePartnerApiHealth.measured_at.desc()).limit(limit).all()


def create_promotion(db: Session, body: PromotionCampaignCreateIn) -> SellerPromotionCampaign:
    get_seller_or_404(db, body.seller_id)
    if not db.get(MarketplaceChannelPartner, body.channel_partner_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="channel_partner_not_found")
    exists = (
        db.query(SellerPromotionCampaign)
        .filter(
            SellerPromotionCampaign.seller_id == body.seller_id,
            SellerPromotionCampaign.campaign_code == body.campaign_code,
        )
        .first()
    )
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="campaign_code_exists")
    row = SellerPromotionCampaign(
        id=new_id(),
        discount_pct=Decimal(str(body.discount_pct)) if body.discount_pct is not None else None,
        **{k: v for k, v in body.model_dump().items() if k != "discount_pct"},
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_promotions(db: Session, seller_id: str, status_filter: str | None = None) -> list[dict]:
    get_seller_or_404(db, seller_id)
    q = db.query(SellerPromotionCampaign).filter(SellerPromotionCampaign.seller_id == seller_id)
    if status_filter:
        q = q.filter(SellerPromotionCampaign.status == status_filter)
    codes = {p.id: p.code for p in db.query(MarketplaceChannelPartner).all()}
    return [
        {**{c.name: getattr(r, c.name) for c in r.__table__.columns}, "partner_code": codes.get(r.channel_partner_id)}
        for r in q.order_by(SellerPromotionCampaign.starts_at.desc()).all()
    ]
