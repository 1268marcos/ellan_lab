from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.finance import (
    BillingProcessedEvent,
    FinanceOpsInvoice,
    FinancePartnerAccount,
    PartnerApiKey,
    PartnerB2bInvoice,
    PartnerBillingCycle,
    PartnerBillingPlan,
    PartnerWebhookEndpoint,
    WalletProviderCatalog,
    WalletTransaction,
)
from app.schemas.finance import (
    ApiKeyListOut,
    ApiKeyMetaOut,
    ApiKeyRotateOut,
    B2bInvoiceIn,
    B2bInvoiceUpdate,
    BillingCycleIn,
    BillingCycleUpdate,
    BillingPlanIn,
    BillingPlanUpdate,
    OpsInvoiceIn,
    OpsInvoiceUpdate,
    PartnerAccountIn,
    PartnerAccountUpdate,
    WalletProviderIn,
    WalletTransactionIn,
    WebhookConfigureIn,
    WebhookOut,
)
from app.services.crypto_util import generate_partner_api_key, hash_secret, new_id


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# --- Partners ---


def list_partners(db: Session, active_only: bool = False) -> list[FinancePartnerAccount]:
    q = db.query(FinancePartnerAccount)
    if active_only:
        q = q.filter(FinancePartnerAccount.active.is_(True))
    return q.order_by(FinancePartnerAccount.code).all()


def get_partner_or_404(db: Session, partner_id: str) -> FinancePartnerAccount:
    row = db.get(FinancePartnerAccount, partner_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="partner_not_found")
    return row


def create_partner(db: Session, body: PartnerAccountIn) -> FinancePartnerAccount:
    if db.query(FinancePartnerAccount).filter(FinancePartnerAccount.code == body.code).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="partner_code_exists")
    pid = body.id or new_id()
    row = FinancePartnerAccount(
        id=pid,
        code=body.code,
        name=body.name,
        partner_type=body.partner_type,
        country_code=body.country_code,
        tax_id=body.tax_id,
        currency=body.currency,
        active=body.active,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_partner(db: Session, partner_id: str, body: PartnerAccountUpdate) -> FinancePartnerAccount:
    row = get_partner_or_404(db, partner_id)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    return row


def delete_partner(db: Session, partner_id: str) -> None:
    row = get_partner_or_404(db, partner_id)
    db.delete(row)
    db.commit()


def configure_webhook(db: Session, partner_id: str, body: WebhookConfigureIn) -> WebhookOut:
    partner = get_partner_or_404(db, partner_id)
    now = _utcnow()
    secret_raw = body.secret or ""
    secret_hash = hash_secret(secret_raw) if secret_raw else hash_secret("unset")
    events = body.events or ["billing.*", "invoice.*"]
    events_json = json.dumps(events)
    existing = (
        db.query(PartnerWebhookEndpoint).filter(PartnerWebhookEndpoint.partner_id == partner_id).first()
    )
    if existing:
        existing.url = body.url
        existing.secret_hash = secret_hash
        if secret_raw:
            existing.secret_key = secret_raw
        existing.events_json = events_json
        existing.active = True
        existing.updated_at = now
        row = existing
    else:
        row = PartnerWebhookEndpoint(
            id=new_id(),
            partner_id=partner_id,
            partner_type=partner.partner_type,
            url=body.url,
            secret_hash=secret_hash,
            secret_key=secret_raw or None,
            events_json=events_json,
            created_at=now,
            updated_at=now,
        )
        db.add(row)
    db.commit()
    db.refresh(row)
    return WebhookOut.model_validate(row)


def get_webhook(db: Session, partner_id: str) -> WebhookOut | None:
    row = db.query(PartnerWebhookEndpoint).filter(PartnerWebhookEndpoint.partner_id == partner_id).first()
    return WebhookOut.model_validate(row) if row else None


def rotate_api_key(db: Session, partner_id: str) -> ApiKeyRotateOut:
    partner = get_partner_or_404(db, partner_id)
    full, prefix, key_hash = generate_partner_api_key(partner.code)
    now = _utcnow()
    for old in db.query(PartnerApiKey).filter(
        PartnerApiKey.partner_id == partner_id, PartnerApiKey.revoked_at.is_(None)
    ):
        old.revoked_at = now
    row = PartnerApiKey(
        id=new_id(),
        partner_id=partner_id,
        partner_type=partner.partner_type,
        key_prefix=prefix,
        key_hash=key_hash,
        label="rotated",
        scopes_json='["billing:read","billing:write","webhooks:receive"]',
        created_at=now,
    )
    db.add(row)
    db.commit()
    return ApiKeyRotateOut(api_key=full, key_prefix=prefix, partner_id=partner_id)


def list_api_keys(db: Session, partner_id: str) -> ApiKeyListOut:
    get_partner_or_404(db, partner_id)
    rows = (
        db.query(PartnerApiKey)
        .filter(PartnerApiKey.partner_id == partner_id)
        .order_by(PartnerApiKey.created_at.desc())
        .all()
    )
    items = [
        ApiKeyMetaOut(
            id=r.id,
            key_prefix=r.key_prefix,
            label=r.label,
            revoked_at=r.revoked_at,
            created_at=r.created_at,
        )
        for r in rows
    ]
    return ApiKeyListOut(items=items)


# --- Billing plans ---


def list_plans(db: Session, partner_id: str | None = None) -> list[PartnerBillingPlan]:
    q = db.query(PartnerBillingPlan)
    if partner_id:
        q = q.filter(PartnerBillingPlan.partner_id == partner_id)
    return q.order_by(PartnerBillingPlan.valid_from.desc()).all()


def create_plan(db: Session, body: BillingPlanIn) -> PartnerBillingPlan:
    get_partner_or_404(db, body.partner_id)
    row = PartnerBillingPlan(id=new_id(), **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_plan(db: Session, plan_id: str, body: BillingPlanUpdate) -> PartnerBillingPlan:
    row = db.get(PartnerBillingPlan, plan_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="plan_not_found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    return row


def delete_plan(db: Session, plan_id: str) -> None:
    row = db.get(PartnerBillingPlan, plan_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="plan_not_found")
    db.delete(row)
    db.commit()


# --- Billing cycles ---


def list_cycles(db: Session, partner_id: str | None = None) -> list[PartnerBillingCycle]:
    q = db.query(PartnerBillingCycle)
    if partner_id:
        q = q.filter(PartnerBillingCycle.partner_id == partner_id)
    return q.order_by(PartnerBillingCycle.period_start.desc()).all()


def create_cycle(db: Session, body: BillingCycleIn) -> PartnerBillingCycle:
    get_partner_or_404(db, body.partner_id)
    if not db.get(PartnerBillingPlan, body.billing_plan_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="plan_not_found")
    row = PartnerBillingCycle(id=new_id(), **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_cycle(db: Session, cycle_id: str, body: BillingCycleUpdate) -> PartnerBillingCycle:
    row = db.get(PartnerBillingCycle, cycle_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="cycle_not_found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    return row


def delete_cycle(db: Session, cycle_id: str) -> None:
    row = db.get(PartnerBillingCycle, cycle_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="cycle_not_found")
    db.delete(row)
    db.commit()


# --- B2B invoices ---


def list_b2b_invoices(db: Session, partner_id: str | None = None) -> list[PartnerB2bInvoice]:
    q = db.query(PartnerB2bInvoice)
    if partner_id:
        q = q.filter(PartnerB2bInvoice.partner_id == partner_id)
    return q.order_by(PartnerB2bInvoice.created_at.desc()).all()


def create_b2b_invoice(db: Session, body: B2bInvoiceIn) -> PartnerB2bInvoice:
    get_partner_or_404(db, body.partner_id)
    if not db.get(PartnerBillingCycle, body.cycle_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="cycle_not_found")
    row = PartnerB2bInvoice(id=new_id(), **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_b2b_invoice(db: Session, invoice_id: str, body: B2bInvoiceUpdate) -> PartnerB2bInvoice:
    row = db.get(PartnerB2bInvoice, invoice_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="invoice_not_found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    return row


def delete_b2b_invoice(db: Session, invoice_id: str) -> None:
    row = db.get(PartnerB2bInvoice, invoice_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="invoice_not_found")
    db.delete(row)
    db.commit()


# --- Wallet ---


def list_wallet_providers(db: Session) -> list[WalletProviderCatalog]:
    return db.query(WalletProviderCatalog).order_by(WalletProviderCatalog.code).all()


def create_wallet_provider(db: Session, body: WalletProviderIn) -> WalletProviderCatalog:
    if db.query(WalletProviderCatalog).filter(WalletProviderCatalog.code == body.code).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="wallet_code_exists")
    row = WalletProviderCatalog(code=body.code, name=body.name, is_active=body.is_active)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_wallet_transactions(db: Session, wallet_id: str | None = None) -> list[WalletTransaction]:
    q = db.query(WalletTransaction)
    if wallet_id:
        q = q.filter(WalletTransaction.wallet_id == wallet_id)
    return q.order_by(WalletTransaction.created_at.desc()).limit(500).all()


def create_wallet_transaction(db: Session, body: WalletTransactionIn) -> WalletTransaction:
    row = WalletTransaction(id=new_id(), **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


# --- Ops invoices ---


def list_ops_invoices(db: Session, order_id: str | None = None) -> list[FinanceOpsInvoice]:
    q = db.query(FinanceOpsInvoice)
    if order_id:
        q = q.filter(FinanceOpsInvoice.order_id == order_id)
    return q.order_by(FinanceOpsInvoice.created_at.desc()).limit(500).all()


def create_ops_invoice(db: Session, body: OpsInvoiceIn) -> FinanceOpsInvoice:
    now = _utcnow()
    iid = body.id or f"inv-{new_id()[:12]}"
    row = FinanceOpsInvoice(
        id=iid,
        order_id=body.order_id,
        country=body.country,
        invoice_type=body.invoice_type,
        status=body.status,
        amount_cents=body.amount_cents,
        currency=body.currency,
        locker_id=body.locker_id,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_ops_invoice(db: Session, invoice_id: str, body: OpsInvoiceUpdate) -> FinanceOpsInvoice:
    row = db.get(FinanceOpsInvoice, invoice_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ops_invoice_not_found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    return row


def list_billing_events(db: Session) -> list[BillingProcessedEvent]:
    return db.query(BillingProcessedEvent).order_by(BillingProcessedEvent.processed_at.desc()).limit(200).all()
