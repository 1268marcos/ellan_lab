from __future__ import annotations

import json

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.privacy_extended import PrivacyTransferRecord
from app.models.privacy_pro import PrivacyTransferWizardSession
from app.schemas.privacy_extended import TransferRecordOut
from app.services.crypto_util import new_id, utcnow
from app.services.privacy_extended_service import get_regulation_by_code

WIZARD_STEPS = ["SCOPE", "MECHANISM", "PROCESSOR", "DOCUMENT", "REVIEW"]
MECHANISMS = ["SCC", "BCR", "ADEQUACY", "DEROGATION", "BINDING_RULES"]


def _session_out(row: PrivacyTransferWizardSession) -> dict:
    return {
        "id": row.id,
        "regulation_code": row.regulation_code,
        "current_step": row.current_step,
        "status": row.status,
        "destination_country": row.destination_country,
        "mechanism": row.mechanism,
        "processor_id": row.processor_id,
        "processing_activity_id": row.processing_activity_id,
        "document_ref": row.document_ref,
        "adequacy_notes": row.adequacy_notes,
        "steps_completed": json.loads(row.steps_completed_json or "[]"),
        "transfer_record_id": row.transfer_record_id,
        "next_step": _next_step(row),
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def _next_step(row: PrivacyTransferWizardSession) -> str | None:
    if row.status != "IN_PROGRESS":
        return None
    try:
        idx = WIZARD_STEPS.index(row.current_step)
    except ValueError:
        return WIZARD_STEPS[0]
    return WIZARD_STEPS[idx + 1] if idx + 1 < len(WIZARD_STEPS) else None


def start_wizard(db: Session, *, regulation_code: str) -> dict:
    get_regulation_by_code(db, regulation_code)
    now = utcnow()
    row = PrivacyTransferWizardSession(
        id=new_id(),
        regulation_code=regulation_code.upper(),
        current_step="SCOPE",
        status="IN_PROGRESS",
        steps_completed_json="[]",
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _session_out(row)


def get_wizard(db: Session, session_id: str) -> dict:
    row = db.get(PrivacyTransferWizardSession, session_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="wizard_session_not_found")
    return _session_out(row)


def advance_wizard_step(
    db: Session,
    session_id: str,
    *,
    step: str,
    destination_country: str | None = None,
    mechanism: str | None = None,
    processor_id: str | None = None,
    processing_activity_id: str | None = None,
    document_ref: str | None = None,
    adequacy_notes: str | None = None,
) -> dict:
    row = db.get(PrivacyTransferWizardSession, session_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="wizard_session_not_found")
    if row.status != "IN_PROGRESS":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="wizard_session_not_active")

    step_u = step.upper()
    if step_u != row.current_step:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"expected_step_{row.current_step}",
        )

    if step_u == "SCOPE":
        if not destination_country or len(destination_country) != 2:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="destination_country_required")
        row.destination_country = destination_country.upper()
    elif step_u == "MECHANISM":
        mech = (mechanism or "").upper()
        if mech not in MECHANISMS:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_mechanism")
        row.mechanism = mech
        if adequacy_notes:
            row.adequacy_notes = adequacy_notes
    elif step_u == "PROCESSOR":
        row.processor_id = processor_id
        row.processing_activity_id = processing_activity_id
    elif step_u == "DOCUMENT":
        if not document_ref:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="document_ref_required")
        row.document_ref = document_ref

    completed = json.loads(row.steps_completed_json or "[]")
    if step_u not in completed:
        completed.append(step_u)
    row.steps_completed_json = json.dumps(completed)

    idx = WIZARD_STEPS.index(step_u)
    row.current_step = WIZARD_STEPS[idx + 1] if idx + 1 < len(WIZARD_STEPS) else "REVIEW"
    row.updated_at = utcnow()
    db.commit()
    db.refresh(row)
    return _session_out(row)


def complete_wizard(db: Session, session_id: str) -> TransferRecordOut:
    row = db.get(PrivacyTransferWizardSession, session_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="wizard_session_not_found")
    if row.current_step != "REVIEW" or row.status != "IN_PROGRESS":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="wizard_not_ready_for_review")
    if not row.destination_country or not row.mechanism or not row.document_ref:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="wizard_incomplete")

    now = utcnow()
    transfer = PrivacyTransferRecord(
        id=new_id(),
        regulation_code=row.regulation_code,
        destination_country=row.destination_country,
        mechanism=row.mechanism,
        processor_id=row.processor_id,
        processing_activity_id=row.processing_activity_id,
        status="ACTIVE",
        document_ref=row.document_ref,
        created_at=now,
        updated_at=now,
    )
    db.add(transfer)
    row.status = "COMPLETED"
    row.transfer_record_id = transfer.id
    row.updated_at = now
    completed = json.loads(row.steps_completed_json or "[]")
    if "REVIEW" not in completed:
        completed.append("REVIEW")
    row.steps_completed_json = json.dumps(completed)
    db.commit()
    db.refresh(transfer)
    return TransferRecordOut.model_validate(transfer)
