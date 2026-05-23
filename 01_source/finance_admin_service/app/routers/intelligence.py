from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.finance_professional import (
    CommercialContractIn,
    CommercialContractListOut,
    CommercialContractOut,
    EcosystemSummaryOut,
    IntegrationMilestoneIn,
    IntegrationMilestoneListOut,
    IntegrationMilestoneOut,
    IntegrationMilestoneUpdate,
    PartnerReadinessOut,
    ReadinessListOut,
    ReadinessRecomputeOut,
    SlaBreachIn,
    SlaBreachListOut,
    SlaBreachOut,
    SlaDefinitionIn,
    SlaDefinitionListOut,
    SlaDefinitionOut,
)
from app.services import finance_professional_service as pro_svc
from app.services.finance_readiness_service import list_readiness, recompute_all_readiness

router = APIRouter(tags=["finance-intelligence"])


@router.get("/locker-network-catalog/ecosystem-summary", response_model=EcosystemSummaryOut)
def ecosystem_summary(db: Session = Depends(get_db)) -> EcosystemSummaryOut:
    data = pro_svc.ecosystem_summary(db)
    data["top_ready"] = [PartnerReadinessOut.model_validate(r) for r in data["top_ready"]]
    return EcosystemSummaryOut(**data)


@router.get("/partner-readiness", response_model=ReadinessListOut)
def get_partner_readiness(
    min_score: int | None = Query(None),
    grade: str | None = Query(None),
    db: Session = Depends(get_db),
) -> ReadinessListOut:
    rows = list_readiness(db, min_score=min_score, grade=grade)
    items = [PartnerReadinessOut.model_validate(r) for r in rows]
    avg = sum(i.readiness_score for i in items) / len(items) if items else 0.0
    return ReadinessListOut(items=items, total=len(items), average_score=round(avg, 2))


@router.post("/partner-readiness/recompute", response_model=ReadinessRecomputeOut)
def recompute_readiness(db: Session = Depends(get_db)) -> ReadinessRecomputeOut:
    n, avg = recompute_all_readiness(db)
    return ReadinessRecomputeOut(recomputed=n, average_score=round(avg, 2))


@router.get("/commercial-contracts", response_model=CommercialContractListOut)
def list_contracts(partner_id: str | None = Query(None), db: Session = Depends(get_db)) -> CommercialContractListOut:
    rows = pro_svc.list_contracts(db, partner_id)
    items = [CommercialContractOut.model_validate(r) for r in rows]
    return CommercialContractListOut(items=items, total=len(items))


@router.post("/commercial-contracts", response_model=CommercialContractOut, status_code=status.HTTP_201_CREATED)
def create_contract(body: CommercialContractIn, db: Session = Depends(get_db)) -> CommercialContractOut:
    return CommercialContractOut.model_validate(pro_svc.create_contract(db, body))


@router.get("/integration-milestones", response_model=IntegrationMilestoneListOut)
def list_milestones(
    catalog_code: str | None = Query(None), db: Session = Depends(get_db)
) -> IntegrationMilestoneListOut:
    rows = pro_svc.list_milestones(db, catalog_code)
    items = [IntegrationMilestoneOut.model_validate(r) for r in rows]
    return IntegrationMilestoneListOut(items=items, total=len(items))


@router.post("/integration-milestones", response_model=IntegrationMilestoneOut, status_code=status.HTTP_201_CREATED)
def create_milestone(body: IntegrationMilestoneIn, db: Session = Depends(get_db)) -> IntegrationMilestoneOut:
    return IntegrationMilestoneOut.model_validate(pro_svc.create_milestone(db, body))


@router.patch("/integration-milestones/{milestone_id}", response_model=IntegrationMilestoneOut)
def update_milestone(
    milestone_id: str, body: IntegrationMilestoneUpdate, db: Session = Depends(get_db)
) -> IntegrationMilestoneOut:
    return IntegrationMilestoneOut.model_validate(pro_svc.update_milestone(db, milestone_id, body))


@router.get("/sla-definitions", response_model=SlaDefinitionListOut)
def list_sla_definitions(
    partner_id: str | None = Query(None), db: Session = Depends(get_db)
) -> SlaDefinitionListOut:
    rows = pro_svc.list_sla_definitions(db, partner_id)
    items = [SlaDefinitionOut.model_validate(r) for r in rows]
    return SlaDefinitionListOut(items=items, total=len(items))


@router.post("/sla-definitions", response_model=SlaDefinitionOut, status_code=status.HTTP_201_CREATED)
def create_sla_definition(body: SlaDefinitionIn, db: Session = Depends(get_db)) -> SlaDefinitionOut:
    return SlaDefinitionOut.model_validate(pro_svc.create_sla_definition(db, body))


@router.get("/sla-breaches", response_model=SlaBreachListOut)
def list_sla_breaches(
    partner_id: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
) -> SlaBreachListOut:
    rows = pro_svc.list_sla_breaches(db, partner_id, status_filter)
    items = [SlaBreachOut.model_validate(r) for r in rows]
    return SlaBreachListOut(items=items, total=len(items))


@router.post("/sla-breaches", response_model=SlaBreachOut, status_code=status.HTTP_201_CREATED)
def create_sla_breach(body: SlaBreachIn, db: Session = Depends(get_db)) -> SlaBreachOut:
    return SlaBreachOut.model_validate(pro_svc.record_sla_breach(db, body))
