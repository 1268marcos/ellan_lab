from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.fiscal import FiscalDocumentIn, FiscalDocumentListOut, FiscalDocumentOut, FiscalDocumentUpdate
from app.services import fiscal_core_service

router = APIRouter(prefix="/fiscal-documents", tags=["fiscal-documents"])


@router.get("", response_model=FiscalDocumentListOut)
def list_documents(
    order_id: str | None = Query(None),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
) -> FiscalDocumentListOut:
    items = fiscal_core_service.list_documents(db, order_id=order_id, limit=limit)
    out = [FiscalDocumentOut.model_validate(i) for i in items]
    return FiscalDocumentListOut(items=out, total=len(out))


@router.post("", response_model=FiscalDocumentOut, status_code=status.HTTP_201_CREATED)
def create_document(body: FiscalDocumentIn, db: Session = Depends(get_db)) -> FiscalDocumentOut:
    return FiscalDocumentOut.model_validate(fiscal_core_service.create_document(db, body))


@router.get("/{doc_id}", response_model=FiscalDocumentOut)
def get_document(doc_id: str, db: Session = Depends(get_db)) -> FiscalDocumentOut:
    return FiscalDocumentOut.model_validate(fiscal_core_service.get_document_or_404(db, doc_id))


@router.patch("/{doc_id}", response_model=FiscalDocumentOut)
def update_document(doc_id: str, body: FiscalDocumentUpdate, db: Session = Depends(get_db)) -> FiscalDocumentOut:
    return FiscalDocumentOut.model_validate(fiscal_core_service.update_document(db, doc_id, body))


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(doc_id: str, db: Session = Depends(get_db)) -> None:
    fiscal_core_service.delete_document(db, doc_id)
