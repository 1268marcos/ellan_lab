from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.privacy_regulatory import (
    DsarDraftOut,
    LiaRecordCreate,
    LiaRecordListOut,
    LiaRecordOut,
    OptOutRecordCreate,
    OptOutRecordListOut,
    OptOutRecordOut,
    RegulatoryObligationListOut,
    RegulatoryObligationOut,
    RegulatoryObligationUpdate,
    RegulatoryToolkitOut,
    RightsCompareOut,
    SubjectRightListOut,
    SubjectRightOut,
)
from app.services.privacy_regulatory_service import (
    build_dsar_draft,
    compare_rights,
    create_lia,
    create_opt_out,
    get_toolkit,
    list_lia,
    list_obligations,
    list_opt_outs,
    list_subject_rights,
    update_obligation,
)

router = APIRouter(tags=["privacy-regulatory"])


@router.get("/regulatory/subject-rights", response_model=SubjectRightListOut)
def get_subject_rights(
    regulation_code: str | None = None,
    db: Session = Depends(get_db),
):
    items, total = list_subject_rights(db, regulation_code)
    return SubjectRightListOut(
        items=[SubjectRightOut.model_validate(i) for i in items],
        total=total,
        regulation_code=regulation_code.upper() if regulation_code else None,
    )


@router.get("/regulatory/obligations", response_model=RegulatoryObligationListOut)
def get_obligations(
    regulation_code: str | None = None,
    category: str | None = None,
    compliance_status: str | None = None,
    db: Session = Depends(get_db),
):
    items, total = list_obligations(db, regulation_code, category, compliance_status)
    return RegulatoryObligationListOut(
        items=[RegulatoryObligationOut.model_validate(i) for i in items],
        total=total,
        regulation_code=regulation_code.upper() if regulation_code else None,
    )


@router.patch("/regulatory/obligations/{obligation_id}", response_model=RegulatoryObligationOut)
def patch_obligation(
    obligation_id: str,
    body: RegulatoryObligationUpdate,
    db: Session = Depends(get_db),
):
    return update_obligation(db, obligation_id, body.model_dump(exclude_unset=True))


@router.get("/regulatory/lia-records", response_model=LiaRecordListOut)
def get_lia_records(
    regulation_code: str | None = None,
    db: Session = Depends(get_db),
):
    items, total = list_lia(db, regulation_code)
    return LiaRecordListOut(items=[LiaRecordOut.model_validate(i) for i in items], total=total)


@router.post("/regulatory/lia-records", response_model=LiaRecordOut, status_code=201)
def post_lia_record(body: LiaRecordCreate, db: Session = Depends(get_db)):
    return create_lia(db, body)


@router.get("/regulatory/opt-out-records", response_model=OptOutRecordListOut)
def get_opt_out_records(
    regulation_code: str | None = None,
    active_only: bool = Query(default=True),
    db: Session = Depends(get_db),
):
    items, total = list_opt_outs(db, regulation_code, active_only)
    return OptOutRecordListOut(items=[OptOutRecordOut.model_validate(i) for i in items], total=total)


@router.post("/regulatory/opt-out-records", response_model=OptOutRecordOut, status_code=201)
def post_opt_out_record(body: OptOutRecordCreate, db: Session = Depends(get_db)):
    return create_opt_out(db, body)


@router.get("/regulatory/toolkit", response_model=RegulatoryToolkitOut)
def get_regulatory_toolkit(
    regulation_code: str = Query(..., min_length=2),
    db: Session = Depends(get_db),
):
    return get_toolkit(db, regulation_code)


@router.get("/regulatory/dsar-draft", response_model=DsarDraftOut)
def get_dsar_draft(
    regulation_code: str = Query(..., min_length=2),
    right_code: str | None = None,
    right_id: str | None = None,
    db: Session = Depends(get_db),
):
    return build_dsar_draft(db, regulation_code=regulation_code, right_code=right_code, right_id=right_id)


@router.get("/regulatory/compare-rights", response_model=RightsCompareOut)
def get_compare_rights(
    codes: str = Query(..., description="Comma-separated codes, e.g. GDPR,LGPD,CCPA"),
    db: Session = Depends(get_db),
):
    return compare_rights(db, [c.strip() for c in codes.split(",") if c.strip()])
