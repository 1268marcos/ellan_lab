from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services import fiscal_global_ops_service, fiscal_intelligence_service, fiscal_readiness_service

router = APIRouter(prefix="/fiscal-global-ops", tags=["fiscal-global-ops"])


class JurisdictionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    country: str
    name: str
    currency: str
    default_regime: str
    vat_label: str
    authority_name: str | None
    active: bool


class CorridorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    corridor_code: str
    name: str
    origin_country: str
    dest_country: str
    primary_issuer_code: str
    fallback_issuer_code: str | None
    document_type_code: str
    service_level: str
    transit_hours_max: int
    active: bool


class CertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    issuer_code: str
    certification_type: str
    status: str
    issuer_authority: str | None
    expires_at: object | None


class SloOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    corridor_code: str
    metric_name: str
    target_p99_ms: int
    target_success_rate_pct: object


class ClassRuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    sku_pattern: str
    ncm_code: str
    cfop: str | None
    country: str
    priority: int


class WebhookDlqOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    issuer_id: str
    event_type: str
    delivery_status: str
    http_status: int | None
    attempt: int
    error_message: str | None
    created_at: object


@router.get("/summary")
def summary(db: Session = Depends(get_db)) -> dict:
    return fiscal_global_ops_service.global_ops_summary(db)


@router.post("/seed-global")
def seed_global(db: Session = Depends(get_db)) -> dict[str, int]:
    return fiscal_global_ops_service.seed_global_ops(db)


@router.get("/jurisdictions")
def list_jurisdictions(db: Session = Depends(get_db)) -> dict:
    items = [JurisdictionOut.model_validate(r) for r in fiscal_global_ops_service.list_jurisdictions(db)]
    return {"items": items, "total": len(items)}


@router.get("/corridors")
def list_corridors(active_only: bool = Query(True), db: Session = Depends(get_db)) -> dict:
    items = [CorridorOut.model_validate(r) for r in fiscal_global_ops_service.list_corridors(db, active_only)]
    return {"items": items, "total": len(items)}


@router.get("/corridors/{corridor_code}")
def get_corridor(corridor_code: str, db: Session = Depends(get_db)) -> dict:
    detail = fiscal_intelligence_service.get_corridor_detail(db, corridor_code)
    if not detail:
        raise HTTPException(status_code=404, detail="corridor not found")
    return detail


@router.get("/certifications")
def list_certifications(
    issuer_id: str | None = Query(None),
    expiring_within_days: int | None = Query(None, ge=1, le=365),
    enriched: bool = Query(False),
    db: Session = Depends(get_db),
) -> dict:
    if enriched or expiring_within_days is not None:
        items = fiscal_intelligence_service.list_certifications_enriched(
            db, issuer_id=issuer_id, expiring_within_days=expiring_within_days
        )
        return {"items": items, "total": len(items)}
    items = [CertOut.model_validate(r) for r in fiscal_global_ops_service.list_certifications(db, issuer_id)]
    return {"items": items, "total": len(items)}


@router.get("/slo-policies")
def list_slos(db: Session = Depends(get_db)) -> dict:
    items = [SloOut.model_validate(r) for r in fiscal_global_ops_service.list_slo_policies(db)]
    return {"items": items, "total": len(items)}


@router.get("/classification-rules")
def list_class_rules(country: str | None = Query(None), db: Session = Depends(get_db)) -> dict:
    items = [ClassRuleOut.model_validate(r) for r in fiscal_global_ops_service.list_classification_rules(db, country)]
    return {"items": items, "total": len(items)}


@router.get("/webhook-deliveries")
def list_webhook_dlq(failed_only: bool = Query(True), limit: int = Query(100, le=500), db: Session = Depends(get_db)) -> dict:
    items = [WebhookDlqOut.model_validate(r) for r in fiscal_global_ops_service.list_webhook_deliveries(db, failed_only, limit)]
    return {"items": items, "total": len(items)}


@router.post("/webhook-deliveries/{delivery_id}/retry")
def retry_webhook(delivery_id: str, db: Session = Depends(get_db)) -> dict:
    row = fiscal_intelligence_service.retry_webhook_delivery(db, delivery_id)
    if not row:
        raise HTTPException(status_code=404, detail="webhook delivery not found")
    return WebhookDlqOut.model_validate(row).model_dump()


@router.post("/classification-rules/test-classify")
def test_classify(
    sku: str = Query(min_length=1),
    country: str = Query("BR", min_length=2, max_length=5),
    db: Session = Depends(get_db),
) -> dict:
    return fiscal_intelligence_service.test_classify_sku(db, sku=sku, country=country)


@router.post("/integration-readiness/recompute")
def recompute_readiness(db: Session = Depends(get_db)) -> dict:
    counts = fiscal_global_ops_service.recompute_readiness(db)
    return counts


@router.get("/integration-readiness")
def list_readiness(band: str | None = Query(None), limit: int = Query(200, le=500), db: Session = Depends(get_db)) -> dict:
    rows = fiscal_readiness_service.list_readiness(db, band=band, limit=limit)
    items = [fiscal_readiness_service.readiness_to_dict(r) for r in rows]
    return {"items": items, "total": len(items)}
