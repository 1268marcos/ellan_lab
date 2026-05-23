from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.privacy_extended import (
    BreachIncidentIn,
    BreachIncidentListOut,
    BreachIncidentOut,
    BreachIncidentUpdate,
    DataCategoryIn,
    DataCategoryListOut,
    DataCategoryOut,
    ImpactAssessmentIn,
    ImpactAssessmentListOut,
    ImpactAssessmentOut,
    ImpactAssessmentUpdate,
    LegalBasisIn,
    LegalBasisListOut,
    LegalBasisOut,
    ProcessingActivityIn,
    ProcessingActivityListOut,
    ProcessingActivityOut,
    ProcessingActivityUpdate,
    ProcessorAgreementIn,
    ProcessorAgreementListOut,
    ProcessorAgreementOut,
    ProcessorIn,
    ProcessorListOut,
    ProcessorOut,
    RegulationHubOut,
    RetentionRuleIn,
    RetentionRuleListOut,
    RetentionRuleOut,
    TransferRecordIn,
    TransferRecordListOut,
    TransferRecordOut,
)
from app.services import privacy_extended_service as svc

router = APIRouter(tags=["privacy-compliance-extended"])


@router.get("/regulations/{regulation_code}/hub", response_model=RegulationHubOut)
def regulation_hub(regulation_code: str, db: Session = Depends(get_db)) -> RegulationHubOut:
    return svc.regulation_hub(db, regulation_code)


@router.get("/legal-bases", response_model=LegalBasisListOut)
def list_legal_bases(
    regulation_code: str | None = Query(None),
    limit: int = Query(200, le=500),
    db: Session = Depends(get_db),
) -> LegalBasisListOut:
    items = [LegalBasisOut.model_validate(r) for r in svc.list_legal_bases(db, regulation_code=regulation_code, limit=limit)]
    return LegalBasisListOut(items=items, total=len(items))


@router.post("/legal-bases", response_model=LegalBasisOut, status_code=status.HTTP_201_CREATED)
def create_legal_basis(body: LegalBasisIn, db: Session = Depends(get_db)) -> LegalBasisOut:
    return LegalBasisOut.model_validate(svc.create_legal_basis(db, body))


@router.get("/data-categories", response_model=DataCategoryListOut)
def list_data_categories(
    regulation_code: str | None = Query(None),
    limit: int = Query(200, le=500),
    db: Session = Depends(get_db),
) -> DataCategoryListOut:
    items = [
        DataCategoryOut.model_validate(r) for r in svc.list_data_categories(db, regulation_code=regulation_code, limit=limit)
    ]
    return DataCategoryListOut(items=items, total=len(items))


@router.post("/data-categories", response_model=DataCategoryOut, status_code=status.HTTP_201_CREATED)
def create_data_category(body: DataCategoryIn, db: Session = Depends(get_db)) -> DataCategoryOut:
    return DataCategoryOut.model_validate(svc.create_data_category(db, body))


@router.get("/processing-activities", response_model=ProcessingActivityListOut)
def list_processing_activities(
    regulation_code: str | None = Query(None),
    limit: int = Query(200, le=500),
    db: Session = Depends(get_db),
) -> ProcessingActivityListOut:
    items = [ProcessingActivityOut.model_validate(r) for r in svc.list_processing_activities(db, regulation_code=regulation_code, limit=limit)]
    return ProcessingActivityListOut(items=items, total=len(items))


@router.post("/processing-activities", response_model=ProcessingActivityOut, status_code=status.HTTP_201_CREATED)
def create_processing_activity(body: ProcessingActivityIn, db: Session = Depends(get_db)) -> ProcessingActivityOut:
    return ProcessingActivityOut.model_validate(svc.create_processing_activity(db, body))


@router.patch("/processing-activities/{activity_id}", response_model=ProcessingActivityOut)
def update_processing_activity(
    activity_id: str, body: ProcessingActivityUpdate, db: Session = Depends(get_db)
) -> ProcessingActivityOut:
    return ProcessingActivityOut.model_validate(svc.update_processing_activity(db, activity_id, body))


@router.get("/processors", response_model=ProcessorListOut)
def list_processors(
    regulation_code: str | None = Query(None),
    limit: int = Query(200, le=500),
    db: Session = Depends(get_db),
) -> ProcessorListOut:
    items = [ProcessorOut.model_validate(r) for r in svc.list_processors(db, regulation_code=regulation_code, limit=limit)]
    return ProcessorListOut(items=items, total=len(items))


@router.post("/processors", response_model=ProcessorOut, status_code=status.HTTP_201_CREATED)
def create_processor(body: ProcessorIn, db: Session = Depends(get_db)) -> ProcessorOut:
    return ProcessorOut.model_validate(svc.create_processor(db, body))


@router.get("/processor-agreements", response_model=ProcessorAgreementListOut)
def list_processor_agreements(
    regulation_code: str | None = Query(None),
    processor_id: str | None = Query(None),
    limit: int = Query(200, le=500),
    db: Session = Depends(get_db),
) -> ProcessorAgreementListOut:
    items = [
        ProcessorAgreementOut.model_validate(r)
        for r in svc.list_processor_agreements(db, regulation_code=regulation_code, processor_id=processor_id, limit=limit)
    ]
    return ProcessorAgreementListOut(items=items, total=len(items))


@router.post("/processor-agreements", response_model=ProcessorAgreementOut, status_code=status.HTTP_201_CREATED)
def create_processor_agreement(body: ProcessorAgreementIn, db: Session = Depends(get_db)) -> ProcessorAgreementOut:
    return ProcessorAgreementOut.model_validate(svc.create_processor_agreement(db, body))


@router.get("/retention-rules", response_model=RetentionRuleListOut)
def list_retention_rules(
    regulation_code: str | None = Query(None),
    limit: int = Query(200, le=500),
    db: Session = Depends(get_db),
) -> RetentionRuleListOut:
    items = [
        RetentionRuleOut.model_validate(r) for r in svc.list_retention_rules(db, regulation_code=regulation_code, limit=limit)
    ]
    return RetentionRuleListOut(items=items, total=len(items))


@router.post("/retention-rules", response_model=RetentionRuleOut, status_code=status.HTTP_201_CREATED)
def create_retention_rule(body: RetentionRuleIn, db: Session = Depends(get_db)) -> RetentionRuleOut:
    return RetentionRuleOut.model_validate(svc.create_retention_rule(db, body))


@router.get("/breach-incidents", response_model=BreachIncidentListOut)
def list_breach_incidents(
    regulation_code: str | None = Query(None),
    limit: int = Query(200, le=500),
    db: Session = Depends(get_db),
) -> BreachIncidentListOut:
    items = [
        BreachIncidentOut.model_validate(r) for r in svc.list_breach_incidents(db, regulation_code=regulation_code, limit=limit)
    ]
    return BreachIncidentListOut(items=items, total=len(items))


@router.post("/breach-incidents", response_model=BreachIncidentOut, status_code=status.HTTP_201_CREATED)
def create_breach_incident(body: BreachIncidentIn, db: Session = Depends(get_db)) -> BreachIncidentOut:
    return BreachIncidentOut.model_validate(svc.create_breach_incident(db, body))


@router.patch("/breach-incidents/{incident_id}", response_model=BreachIncidentOut)
def update_breach_incident(
    incident_id: str, body: BreachIncidentUpdate, db: Session = Depends(get_db)
) -> BreachIncidentOut:
    return BreachIncidentOut.model_validate(svc.update_breach_incident(db, incident_id, body))


@router.get("/impact-assessments", response_model=ImpactAssessmentListOut)
def list_impact_assessments(
    regulation_code: str | None = Query(None),
    limit: int = Query(200, le=500),
    db: Session = Depends(get_db),
) -> ImpactAssessmentListOut:
    items = [
        ImpactAssessmentOut.model_validate(r)
        for r in svc.list_impact_assessments(db, regulation_code=regulation_code, limit=limit)
    ]
    return ImpactAssessmentListOut(items=items, total=len(items))


@router.post("/impact-assessments", response_model=ImpactAssessmentOut, status_code=status.HTTP_201_CREATED)
def create_impact_assessment(body: ImpactAssessmentIn, db: Session = Depends(get_db)) -> ImpactAssessmentOut:
    return ImpactAssessmentOut.model_validate(svc.create_impact_assessment(db, body))


@router.patch("/impact-assessments/{assessment_id}", response_model=ImpactAssessmentOut)
def update_impact_assessment(
    assessment_id: str, body: ImpactAssessmentUpdate, db: Session = Depends(get_db)
) -> ImpactAssessmentOut:
    return ImpactAssessmentOut.model_validate(svc.update_impact_assessment(db, assessment_id, body))


@router.get("/transfer-records", response_model=TransferRecordListOut)
def list_transfer_records(
    regulation_code: str | None = Query(None),
    limit: int = Query(200, le=500),
    db: Session = Depends(get_db),
) -> TransferRecordListOut:
    items = [
        TransferRecordOut.model_validate(r) for r in svc.list_transfer_records(db, regulation_code=regulation_code, limit=limit)
    ]
    return TransferRecordListOut(items=items, total=len(items))


@router.post("/transfer-records", response_model=TransferRecordOut, status_code=status.HTTP_201_CREATED)
def create_transfer_record(body: TransferRecordIn, db: Session = Depends(get_db)) -> TransferRecordOut:
    return TransferRecordOut.model_validate(svc.create_transfer_record(db, body))
