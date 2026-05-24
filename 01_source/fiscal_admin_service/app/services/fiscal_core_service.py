from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.fiscal_core import (
    FiscalAccountingApproval,
    FiscalAuthorityCallback,
    FiscalDocument,
    FiscalProviderHealthStatus,
    FiscalReconciliationGap,
    ProductFiscalConfig,
    TenantFiscalConfig,
)
from app.schemas.fiscal import (
    ApprovalIn,
    FiscalDocumentIn,
    FiscalDocumentUpdate,
    GapIn,
    GapUpdate,
    ProductFiscalIn,
    ProviderHealthIn,
    TenantFiscalIn,
)
from app.services.crypto_util import new_id


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# Documents
def list_documents(db: Session, *, order_id: str | None = None, limit: int = 100) -> list[FiscalDocument]:
    q = db.query(FiscalDocument)
    if order_id:
        q = q.filter(FiscalDocument.order_id == order_id)
    return q.order_by(FiscalDocument.issued_at.desc()).limit(limit).all()


def create_document(db: Session, body: FiscalDocumentIn) -> FiscalDocument:
    now = _utcnow()
    doc_id = body.id or f"fd-{new_id()[:12]}"
    row = FiscalDocument(
        id=doc_id,
        order_id=body.order_id,
        receipt_code=body.receipt_code,
        document_type=body.document_type,
        channel=body.channel,
        region=body.region,
        amount_cents=body.amount_cents,
        currency=body.currency,
        delivery_mode=body.delivery_mode,
        send_status=body.send_status,
        payload_json=body.payload_json,
        issued_at=now,
        created_at=now,
        updated_at=now,
        tenant_id=body.tenant_id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_document_or_404(db: Session, doc_id: str) -> FiscalDocument:
    row = db.get(FiscalDocument, doc_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="document_not_found")
    return row


def update_document(db: Session, doc_id: str, body: FiscalDocumentUpdate) -> FiscalDocument:
    row = get_document_or_404(db, doc_id)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    return row


def delete_document(db: Session, doc_id: str) -> None:
    row = get_document_or_404(db, doc_id)
    db.delete(row)
    db.commit()


# Gaps
def list_gaps(db: Session, *, status: str | None = None, limit: int = 100) -> list[FiscalReconciliationGap]:
    q = db.query(FiscalReconciliationGap)
    if status:
        q = q.filter(FiscalReconciliationGap.status == status)
    return q.order_by(FiscalReconciliationGap.last_detected_at.desc()).limit(limit).all()


def create_gap(db: Session, body: GapIn) -> FiscalReconciliationGap:
    now = _utcnow()
    row = FiscalReconciliationGap(
        id=body.id or f"gap-{new_id()[:12]}",
        dedupe_key=body.dedupe_key,
        gap_type=body.gap_type,
        severity=body.severity,
        status=body.status,
        order_id=body.order_id,
        invoice_id=body.invoice_id,
        details_json=body.details_json,
        first_detected_at=now,
        last_detected_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def patch_gap(db: Session, gap_id: str, body: GapUpdate) -> FiscalReconciliationGap:
    row = db.get(FiscalReconciliationGap, gap_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="gap_not_found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    if body.status == "RESOLVED":
        row.resolved_at = _utcnow()
    row.last_detected_at = _utcnow()
    db.commit()
    db.refresh(row)
    return row


# Provider health
def list_provider_health(db: Session) -> list[FiscalProviderHealthStatus]:
    return db.query(FiscalProviderHealthStatus).order_by(FiscalProviderHealthStatus.country).all()


def upsert_provider_health(db: Session, body: ProviderHealthIn) -> FiscalProviderHealthStatus:
    now = _utcnow()
    row = db.get(FiscalProviderHealthStatus, body.country)
    if row:
        row.provider_name = body.provider_name
        row.mode = body.mode
        row.enabled = body.enabled
        row.base_url = body.base_url
        row.last_status = body.last_status
        row.checked_at = now
    else:
        row = FiscalProviderHealthStatus(
            country=body.country,
            provider_name=body.provider_name,
            mode=body.mode,
            enabled=body.enabled,
            base_url=body.base_url,
            last_status=body.last_status,
            checked_at=now,
        )
        db.add(row)
    db.commit()
    db.refresh(row)
    return row


# Tenant / product config
def list_tenants(db: Session, limit: int = 100) -> list[TenantFiscalConfig]:
    return db.query(TenantFiscalConfig).limit(limit).all()


def upsert_tenant(db: Session, body: TenantFiscalIn) -> TenantFiscalConfig:
    row = db.get(TenantFiscalConfig, body.tenant_id)
    data = body.model_dump()
    if row:
        for k, v in data.items():
            setattr(row, k, v)
    else:
        row = TenantFiscalConfig(**data, created_at=_utcnow())
        db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_products(db: Session, limit: int = 100) -> list[ProductFiscalConfig]:
    return db.query(ProductFiscalConfig).limit(limit).all()


def upsert_product(db: Session, body: ProductFiscalIn) -> ProductFiscalConfig:
    row = db.get(ProductFiscalConfig, body.sku_id)
    data = body.model_dump()
    if row:
        for k, v in data.items():
            setattr(row, k, v)
        row.updated_at = _utcnow()
    else:
        row = ProductFiscalConfig(**data)
        db.add(row)
    db.commit()
    db.refresh(row)
    return row


# Approvals & callbacks
def list_approvals(db: Session, limit: int = 100) -> list[FiscalAccountingApproval]:
    return db.query(FiscalAccountingApproval).order_by(FiscalAccountingApproval.created_at.desc()).limit(limit).all()


def create_approval(db: Session, body: ApprovalIn) -> FiscalAccountingApproval:
    row = FiscalAccountingApproval(
        id=body.id or f"appr-{new_id()[:12]}",
        owner=body.owner,
        status=body.status,
        eta=body.eta,
        payload_json=body.payload_json,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_callbacks(db: Session, limit: int = 100) -> list[FiscalAuthorityCallback]:
    return (
        db.query(FiscalAuthorityCallback).order_by(FiscalAuthorityCallback.received_at.desc()).limit(limit).all()
    )
