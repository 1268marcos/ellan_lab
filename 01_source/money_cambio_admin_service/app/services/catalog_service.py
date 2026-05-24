from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.catalog import (
    PaymentInterfaceCatalog,
    PaymentMethodCatalog,
    PaymentMethodUiAlias,
    WalletProviderCatalog,
)
from app.schemas.catalog import (
    PaymentInterfaceCatalogIn,
    PaymentInterfaceCatalogUpdate,
    PaymentMethodCatalogIn,
    PaymentMethodCatalogUpdate,
    PaymentMethodUiAliasIn,
    PaymentMethodUiAliasUpdate,
    WalletProviderCatalogIn,
    WalletProviderCatalogUpdate,
)
from app.services.crypto_util import new_id


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _dump_json(data: dict | None) -> dict:
    return data if data is not None else {}


# --- payment_method_catalog ---


def list_methods(db: Session, active_only: bool = False) -> list[PaymentMethodCatalog]:
    q = db.query(PaymentMethodCatalog)
    if active_only:
        q = q.filter(PaymentMethodCatalog.is_active.is_(True))
    return q.order_by(PaymentMethodCatalog.code).all()


def create_method(db: Session, body: PaymentMethodCatalogIn) -> PaymentMethodCatalog:
    if db.query(PaymentMethodCatalog).filter(PaymentMethodCatalog.code == body.code).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="method_code_exists")
    row = PaymentMethodCatalog(**body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_method_or_404(db: Session, item_id: int) -> PaymentMethodCatalog:
    row = db.get(PaymentMethodCatalog, item_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="method_not_found")
    return row


def update_method(db: Session, item_id: int, body: PaymentMethodCatalogUpdate) -> PaymentMethodCatalog:
    row = get_method_or_404(db, item_id)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    return row


def delete_method(db: Session, item_id: int) -> None:
    row = get_method_or_404(db, item_id)
    db.delete(row)
    db.commit()


# --- payment_interface_catalog ---


def list_interfaces(db: Session, active_only: bool = False) -> list[PaymentInterfaceCatalog]:
    q = db.query(PaymentInterfaceCatalog)
    if active_only:
        q = q.filter(PaymentInterfaceCatalog.is_active.is_(True))
    return q.order_by(PaymentInterfaceCatalog.code).all()


def create_interface(db: Session, body: PaymentInterfaceCatalogIn) -> PaymentInterfaceCatalog:
    if db.query(PaymentInterfaceCatalog).filter(PaymentInterfaceCatalog.code == body.code).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="interface_code_exists")
    row = PaymentInterfaceCatalog(**body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_interface_or_404(db: Session, item_id: int) -> PaymentInterfaceCatalog:
    row = db.get(PaymentInterfaceCatalog, item_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="interface_not_found")
    return row


def update_interface(db: Session, item_id: int, body: PaymentInterfaceCatalogUpdate) -> PaymentInterfaceCatalog:
    row = get_interface_or_404(db, item_id)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    return row


def delete_interface(db: Session, item_id: int) -> None:
    row = get_interface_or_404(db, item_id)
    db.delete(row)
    db.commit()


# --- payment_method_ui_alias ---


def list_aliases(db: Session, active_only: bool = False) -> list[PaymentMethodUiAlias]:
    q = db.query(PaymentMethodUiAlias)
    if active_only:
        q = q.filter(PaymentMethodUiAlias.is_active.is_(True))
    return q.order_by(PaymentMethodUiAlias.ui_code).all()


def create_alias(db: Session, body: PaymentMethodUiAliasIn) -> PaymentMethodUiAlias:
    aid = body.id or new_id()
    if db.get(PaymentMethodUiAlias, aid):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="alias_id_exists")
    data = body.model_dump(exclude={"id"})
    row = PaymentMethodUiAlias(id=aid, **data)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_alias_or_404(db: Session, alias_id: str) -> PaymentMethodUiAlias:
    row = db.get(PaymentMethodUiAlias, alias_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="alias_not_found")
    return row


def update_alias(db: Session, alias_id: str, body: PaymentMethodUiAliasUpdate) -> PaymentMethodUiAlias:
    row = get_alias_or_404(db, alias_id)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    return row


def delete_alias(db: Session, alias_id: str) -> None:
    row = get_alias_or_404(db, alias_id)
    db.delete(row)
    db.commit()


# --- wallet_provider_catalog ---


def list_wallets(db: Session, active_only: bool = False) -> list[WalletProviderCatalog]:
    q = db.query(WalletProviderCatalog)
    if active_only:
        q = q.filter(WalletProviderCatalog.is_active.is_(True))
    return q.order_by(WalletProviderCatalog.code).all()


def create_wallet(db: Session, body: WalletProviderCatalogIn) -> WalletProviderCatalog:
    if db.query(WalletProviderCatalog).filter(WalletProviderCatalog.code == body.code).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="wallet_code_exists")
    row = WalletProviderCatalog(**body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_wallet_or_404(db: Session, item_id: int) -> WalletProviderCatalog:
    row = db.get(WalletProviderCatalog, item_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="wallet_not_found")
    return row


def update_wallet(db: Session, item_id: int, body: WalletProviderCatalogUpdate) -> WalletProviderCatalog:
    row = get_wallet_or_404(db, item_id)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    return row


def delete_wallet(db: Session, item_id: int) -> None:
    row = get_wallet_or_404(db, item_id)
    db.delete(row)
    db.commit()
