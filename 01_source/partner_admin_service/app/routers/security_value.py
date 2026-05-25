from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.security_value import (
    AccessMatrixOut,
    AccessReviewCampaignCreateIn,
    AccessReviewCampaignListOut,
    AccessReviewCampaignOut,
    AccessReviewDecisionIn,
    AccessReviewItemListOut,
    AlertListOut,
    AlertOut,
    ApplyRoleTemplateIn,
    ApplyRoleTemplateOut,
    BreakGlassCreateIn,
    BreakGlassListOut,
    BreakGlassOut,
    ComplianceListOut,
    RiskScoreListOut,
    RoleTemplateListOut,
    SecurityIntelligenceOut,
)
from app.services import security_value_service

router = APIRouter(prefix="/security-admin/value", tags=["security-value"])


@router.get("/intelligence", response_model=SecurityIntelligenceOut)
def security_intelligence(db: Session = Depends(get_db)) -> SecurityIntelligenceOut:
    return security_value_service.get_security_intelligence(db)


@router.get("/risk-scores", response_model=RiskScoreListOut)
def risk_scores(tier: Optional[str] = Query(None), db: Session = Depends(get_db)) -> RiskScoreListOut:
    return security_value_service.list_risk_scores(db, tier)


@router.post("/risk-scores/compute")
def compute_risks(db: Session = Depends(get_db)) -> dict:
    return security_value_service.compute_risk_scores(db)


@router.get("/role-templates", response_model=RoleTemplateListOut)
def role_templates(db: Session = Depends(get_db)) -> RoleTemplateListOut:
    return security_value_service.list_role_templates(db)


@router.post("/role-templates/apply", response_model=ApplyRoleTemplateOut)
def apply_template(body: ApplyRoleTemplateIn, db: Session = Depends(get_db)) -> ApplyRoleTemplateOut:
    return security_value_service.apply_role_template(db, body)


@router.get("/access-reviews", response_model=AccessReviewCampaignListOut)
def list_campaigns(db: Session = Depends(get_db)) -> AccessReviewCampaignListOut:
    return security_value_service.list_campaigns(db)


@router.post("/access-reviews", response_model=AccessReviewCampaignOut, status_code=status.HTTP_201_CREATED)
def create_campaign(body: AccessReviewCampaignCreateIn, db: Session = Depends(get_db)) -> AccessReviewCampaignOut:
    return security_value_service.create_access_review_campaign(db, body)


@router.get("/access-reviews/{campaign_id}/items", response_model=AccessReviewItemListOut)
def review_items(
    campaign_id: str,
    pending_only: bool = Query(False),
    db: Session = Depends(get_db),
) -> AccessReviewItemListOut:
    return security_value_service.list_review_items(db, campaign_id, pending_only)


@router.post("/access-reviews/items/{item_id}/decide")
def decide_item(item_id: str, body: AccessReviewDecisionIn, db: Session = Depends(get_db)):
    return security_value_service.decide_review_item(db, item_id, body)


@router.get("/break-glass", response_model=BreakGlassListOut)
def list_break_glass(active_only: bool = Query(True), db: Session = Depends(get_db)) -> BreakGlassListOut:
    return security_value_service.list_break_glass(db, active_only)


@router.post("/break-glass", response_model=BreakGlassOut, status_code=status.HTTP_201_CREATED)
def open_break_glass(body: BreakGlassCreateIn, db: Session = Depends(get_db)) -> BreakGlassOut:
    return security_value_service.create_break_glass(db, body)


@router.get("/alerts", response_model=AlertListOut)
def list_alerts(status: Optional[str] = Query("OPEN"), db: Session = Depends(get_db)) -> AlertListOut:
    return security_value_service.list_alerts(db, status)


@router.post("/alerts/{alert_id}/acknowledge", response_model=AlertOut)
def ack_alert(alert_id: str, actor_id: Optional[str] = Query(None), db: Session = Depends(get_db)) -> AlertOut:
    return security_value_service.acknowledge_alert(db, alert_id, actor_id)


@router.get("/compliance", response_model=ComplianceListOut)
def compliance(db: Session = Depends(get_db)) -> ComplianceListOut:
    return security_value_service.list_compliance(db)


@router.get("/access-matrix", response_model=AccessMatrixOut)
def access_matrix(db: Session = Depends(get_db)) -> AccessMatrixOut:
    return security_value_service.build_access_matrix(db)


@router.post("/seed")
def seed_value(db: Session = Depends(get_db)) -> dict:
    return security_value_service.seed_value_layer(db)
