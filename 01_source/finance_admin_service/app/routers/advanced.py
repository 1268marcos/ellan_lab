from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.finance_advanced import (
    AuditLogListOut,
    AuditLogOut,
    CommercialTierIn,
    CommercialTierListOut,
    CommercialTierOut,
    DunningCaseListOut,
    DunningCaseOut,
    DunningPolicyIn,
    DunningPolicyListOut,
    DunningPolicyOut,
    DunningScanOut,
    FxConvertOut,
    FxRateIn,
    FxRateListOut,
    FxRateOut,
    InvoiceDocumentIn,
    InvoiceDocumentListOut,
    InvoiceDocumentOut,
    PaymentTermsIn,
    PaymentTermsListOut,
    PaymentTermsOut,
    ReconciliationMatchOut,
    ReconciliationResultOut,
    ReconciliationRunOut,
    TaxCorridorIn,
    TaxCorridorListOut,
    TaxCorridorOut,
    TierAssignmentIn,
    TierAssignmentListOut,
    TierAssignmentOut,
)
from app.services import finance_advanced_service as adv_svc
from app.services.finance_audit_service import list_audit_log

router = APIRouter(tags=["finance-advanced"])


@router.get("/payment-terms", response_model=PaymentTermsListOut)
def list_payment_terms(partner_id: str | None = Query(None), db: Session = Depends(get_db)) -> PaymentTermsListOut:
    rows = adv_svc.list_payment_terms(db, partner_id)
    return PaymentTermsListOut(items=[PaymentTermsOut.model_validate(r) for r in rows], total=len(rows))


@router.post("/payment-terms", response_model=PaymentTermsOut, status_code=status.HTTP_201_CREATED)
def create_payment_terms(body: PaymentTermsIn, db: Session = Depends(get_db)) -> PaymentTermsOut:
    return PaymentTermsOut.model_validate(adv_svc.create_payment_terms(db, body))


@router.get("/fx-rates", response_model=FxRateListOut)
def list_fx_rates(
    base_currency: str | None = Query(None, alias="base"),
    quote_currency: str | None = Query(None, alias="quote"),
    db: Session = Depends(get_db),
) -> FxRateListOut:
    rows = adv_svc.list_fx_rates(db, base_currency, quote_currency)
    return FxRateListOut(items=[FxRateOut.model_validate(r) for r in rows], total=len(rows))


@router.post("/fx-rates", response_model=FxRateOut, status_code=status.HTTP_201_CREATED)
def create_fx_rate(body: FxRateIn, db: Session = Depends(get_db)) -> FxRateOut:
    return FxRateOut.model_validate(adv_svc.upsert_fx_rate(db, body))


@router.get("/fx-rates/convert", response_model=FxConvertOut)
def convert_fx(
    amount_cents: int = Query(..., ge=0),
    from_currency: str = Query(..., alias="from"),
    to_currency: str = Query(..., alias="to"),
    on_date: date | None = Query(None),
    db: Session = Depends(get_db),
) -> FxConvertOut:
    return FxConvertOut(**adv_svc.convert_cents(db, amount_cents, from_currency, to_currency, on_date))


@router.get("/commercial-tiers", response_model=CommercialTierListOut)
def list_commercial_tiers(db: Session = Depends(get_db)) -> CommercialTierListOut:
    rows = adv_svc.list_tiers(db)
    return CommercialTierListOut(items=[CommercialTierOut.model_validate(r) for r in rows], total=len(rows))


@router.post("/commercial-tiers", response_model=CommercialTierOut, status_code=status.HTTP_201_CREATED)
def upsert_commercial_tier(body: CommercialTierIn, db: Session = Depends(get_db)) -> CommercialTierOut:
    return CommercialTierOut.model_validate(adv_svc.upsert_tier(db, body))


@router.get("/tier-assignments", response_model=TierAssignmentListOut)
def list_tier_assignments(partner_id: str | None = Query(None), db: Session = Depends(get_db)) -> TierAssignmentListOut:
    rows = adv_svc.list_tier_assignments(db, partner_id)
    return TierAssignmentListOut(items=[TierAssignmentOut.model_validate(r) for r in rows], total=len(rows))


@router.post("/tier-assignments", response_model=TierAssignmentOut, status_code=status.HTTP_201_CREATED)
def create_tier_assignment(body: TierAssignmentIn, db: Session = Depends(get_db)) -> TierAssignmentOut:
    return TierAssignmentOut.model_validate(adv_svc.assign_tier(db, body))


@router.get("/dunning-policies", response_model=DunningPolicyListOut)
def list_dunning_policies(db: Session = Depends(get_db)) -> DunningPolicyListOut:
    rows = adv_svc.list_dunning_policies(db)
    return DunningPolicyListOut(items=[DunningPolicyOut.model_validate(r) for r in rows], total=len(rows))


@router.post("/dunning-policies", response_model=DunningPolicyOut, status_code=status.HTTP_201_CREATED)
def create_dunning_policy(body: DunningPolicyIn, db: Session = Depends(get_db)) -> DunningPolicyOut:
    return DunningPolicyOut.model_validate(adv_svc.create_dunning_policy(db, body))


@router.get("/dunning-cases", response_model=DunningCaseListOut)
def list_dunning_cases(status_filter: str | None = Query(None, alias="status"), db: Session = Depends(get_db)) -> DunningCaseListOut:
    rows = adv_svc.list_dunning_cases(db, status_filter)
    return DunningCaseListOut(items=[DunningCaseOut.model_validate(r) for r in rows], total=len(rows))


@router.post("/dunning/scan", response_model=DunningScanOut)
def scan_dunning(db: Session = Depends(get_db)) -> DunningScanOut:
    return DunningScanOut(**adv_svc.scan_overdue_invoices(db))


@router.get("/tax-corridors", response_model=TaxCorridorListOut)
def list_tax_corridors(partner_id: str | None = Query(None), db: Session = Depends(get_db)) -> TaxCorridorListOut:
    rows = adv_svc.list_tax_corridors(db, partner_id)
    return TaxCorridorListOut(items=[TaxCorridorOut.model_validate(r) for r in rows], total=len(rows))


@router.post("/tax-corridors", response_model=TaxCorridorOut, status_code=status.HTTP_201_CREATED)
def create_tax_corridor(body: TaxCorridorIn, db: Session = Depends(get_db)) -> TaxCorridorOut:
    return TaxCorridorOut.model_validate(adv_svc.create_tax_corridor(db, body))


@router.get("/invoice-documents", response_model=InvoiceDocumentListOut)
def list_invoice_documents(invoice_id: str | None = Query(None), db: Session = Depends(get_db)) -> InvoiceDocumentListOut:
    rows = adv_svc.list_invoice_documents(db, invoice_id)
    return InvoiceDocumentListOut(items=[InvoiceDocumentOut.model_validate(r) for r in rows], total=len(rows))


@router.post("/invoice-documents", response_model=InvoiceDocumentOut, status_code=status.HTTP_201_CREATED)
def create_invoice_document(body: InvoiceDocumentIn, db: Session = Depends(get_db)) -> InvoiceDocumentOut:
    return InvoiceDocumentOut.model_validate(adv_svc.create_invoice_document(db, body))


@router.post("/settlement-batches/{batch_id}/reconcile", response_model=ReconciliationResultOut)
def reconcile_settlement(batch_id: str, db: Session = Depends(get_db)) -> ReconciliationResultOut:
    result = adv_svc.reconcile_settlement_batch(db, batch_id)
    return ReconciliationResultOut(
        run=ReconciliationRunOut.model_validate(result["run"]),
        matches=[ReconciliationMatchOut.model_validate(m) for m in result["matches"]],
    )


@router.get("/audit-log", response_model=AuditLogListOut)
def get_audit_log(
    entity_type: str | None = Query(None),
    entity_id: str | None = Query(None),
    db: Session = Depends(get_db),
) -> AuditLogListOut:
    rows = list_audit_log(db, entity_type=entity_type, entity_id=entity_id)
    return AuditLogListOut(items=[AuditLogOut.model_validate(r) for r in rows], total=len(rows))
