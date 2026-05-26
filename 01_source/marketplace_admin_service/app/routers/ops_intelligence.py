from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.marketplace_ops_intelligence import (
    CatalogSyncJobCreateIn,
    CatalogSyncJobListOut,
    CatalogSyncJobOut,
    CrossBorderProfileCreateIn,
    CrossBorderProfileListOut,
    CrossBorderProfileOut,
    OpsIntelligenceSummaryOut,
    OpsPlaybookListOut,
    OpsPlaybookOut,
    PartnerApiHealthListOut,
    PartnerApiHealthOut,
    PromotionCampaignCreateIn,
    PromotionCampaignListOut,
    PromotionCampaignOut,
    SellerChannelQuotaListOut,
    SellerChannelQuotaOut,
    SellerHealthListOut,
    SellerHealthSnapshotOut,
)
from app.models.marketplace_extended import MarketplaceChannelPartner
from app.services import ops_intelligence_service

router = APIRouter(tags=["ops-intelligence"])


def _partner_codes(db: Session) -> dict[str, str]:
    return {p.id: p.code for p in db.query(MarketplaceChannelPartner).all()}


@router.post("/ops-intelligence/seed")
def seed_ops_intelligence(db: Session = Depends(get_db)) -> dict:
    return ops_intelligence_service.seed_ops_intelligence(db)


@router.get("/ops-intelligence/summary", response_model=OpsIntelligenceSummaryOut)
def ops_summary(db: Session = Depends(get_db)) -> OpsIntelligenceSummaryOut:
    return OpsIntelligenceSummaryOut.model_validate(ops_intelligence_service.get_summary(db))


@router.get("/ops-intelligence/playbooks", response_model=OpsPlaybookListOut)
def list_playbooks(
    trigger_type: str | None = Query(None),
    db: Session = Depends(get_db),
) -> OpsPlaybookListOut:
    rows = ops_intelligence_service.list_playbooks(db, trigger_type=trigger_type)
    playbooks = [OpsPlaybookOut.model_validate(ops_intelligence_service.playbook_out(r)) for r in rows]
    return OpsPlaybookListOut(playbooks=playbooks, total=len(playbooks))


@router.post("/sellers/{seller_id}/health/compute", response_model=SellerHealthSnapshotOut)
def compute_health(seller_id: str, db: Session = Depends(get_db)) -> SellerHealthSnapshotOut:
    row = ops_intelligence_service.compute_seller_health(db, seller_id)
    return SellerHealthSnapshotOut.model_validate(ops_intelligence_service.health_out(row))


@router.get("/sellers/{seller_id}/health", response_model=SellerHealthListOut)
def list_health(seller_id: str, db: Session = Depends(get_db)) -> SellerHealthListOut:
    rows = ops_intelligence_service.list_health(db, seller_id)
    snapshots = [SellerHealthSnapshotOut.model_validate(ops_intelligence_service.health_out(r)) for r in rows]
    return SellerHealthListOut(snapshots=snapshots, total=len(snapshots))


@router.get("/sellers/{seller_id}/channel-quotas", response_model=SellerChannelQuotaListOut)
def list_quotas(seller_id: str, db: Session = Depends(get_db)) -> SellerChannelQuotaListOut:
    rows = ops_intelligence_service.list_quotas(db, seller_id)
    quotas = [SellerChannelQuotaOut.model_validate(r) for r in rows]
    return SellerChannelQuotaListOut(quotas=quotas, total=len(quotas))


@router.get("/seller-catalog-sync-jobs", response_model=CatalogSyncJobListOut)
def list_sync_jobs(
    seller_id: str | None = Query(None),
    status: str | None = Query(None),
    db: Session = Depends(get_db),
) -> CatalogSyncJobListOut:
    rows = ops_intelligence_service.list_sync_jobs(db, seller_id=seller_id, status_filter=status)
    jobs = [CatalogSyncJobOut.model_validate(r) for r in rows]
    return CatalogSyncJobListOut(jobs=jobs, total=len(jobs))


@router.post("/seller-catalog-sync-jobs", response_model=CatalogSyncJobOut, status_code=status.HTTP_201_CREATED)
def create_sync_job(body: CatalogSyncJobCreateIn, db: Session = Depends(get_db)) -> CatalogSyncJobOut:
    row = ops_intelligence_service.create_sync_job(db, body)
    return CatalogSyncJobOut.model_validate(
        ops_intelligence_service.sync_job_out(row, _partner_codes(db).get(row.channel_partner_id))
    )


@router.post("/seller-catalog-sync-jobs/{job_id}/run", response_model=CatalogSyncJobOut)
def run_sync_job(job_id: str, db: Session = Depends(get_db)) -> CatalogSyncJobOut:
    row = ops_intelligence_service.run_sync_job(db, job_id)
    return CatalogSyncJobOut.model_validate(
        ops_intelligence_service.sync_job_out(row, _partner_codes(db).get(row.channel_partner_id))
    )


@router.get("/sellers/{seller_id}/cross-border-profiles", response_model=CrossBorderProfileListOut)
def list_cross_border(seller_id: str, db: Session = Depends(get_db)) -> CrossBorderProfileListOut:
    rows = ops_intelligence_service.list_cross_border(db, seller_id)
    profiles = [CrossBorderProfileOut.model_validate(r) for r in rows]
    return CrossBorderProfileListOut(profiles=profiles, total=len(profiles))


@router.post(
    "/sellers/{seller_id}/cross-border-profiles",
    response_model=CrossBorderProfileOut,
    status_code=status.HTTP_201_CREATED,
)
def create_cross_border(
    seller_id: str,
    body: CrossBorderProfileCreateIn,
    db: Session = Depends(get_db),
) -> CrossBorderProfileOut:
    payload = body.model_copy(update={"seller_id": seller_id})
    row = ops_intelligence_service.create_cross_border(db, payload)
    return CrossBorderProfileOut.model_validate(row)


@router.get("/ops-intelligence/partner-api-health", response_model=PartnerApiHealthListOut)
def list_api_health(
    degraded_only: bool = Query(False),
    db: Session = Depends(get_db),
) -> PartnerApiHealthListOut:
    rows = ops_intelligence_service.list_api_health(db, degraded_only=degraded_only)
    snapshots = [PartnerApiHealthOut.model_validate(r) for r in rows]
    return PartnerApiHealthListOut(snapshots=snapshots, total=len(snapshots))


@router.get("/sellers/{seller_id}/promotions", response_model=PromotionCampaignListOut)
def list_promotions(
    seller_id: str,
    status: str | None = Query(None),
    db: Session = Depends(get_db),
) -> PromotionCampaignListOut:
    rows = ops_intelligence_service.list_promotions(db, seller_id, status_filter=status)
    campaigns = [PromotionCampaignOut.model_validate(r) for r in rows]
    return PromotionCampaignListOut(campaigns=campaigns, total=len(campaigns))


@router.post(
    "/sellers/{seller_id}/promotions",
    response_model=PromotionCampaignOut,
    status_code=status.HTTP_201_CREATED,
)
def create_promotion(
    seller_id: str,
    body: PromotionCampaignCreateIn,
    db: Session = Depends(get_db),
) -> PromotionCampaignOut:
    payload = body.model_copy(update={"seller_id": seller_id})
    row = ops_intelligence_service.create_promotion(db, payload)
    return PromotionCampaignOut.model_validate(
        {**{c.name: getattr(row, c.name) for c in row.__table__.columns}, "partner_code": _partner_codes(db).get(row.channel_partner_id)}
    )
