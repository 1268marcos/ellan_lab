from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.contact import PartnerContact
from app.schemas.partner import PartnerContactCreateIn, PartnerContactListOut, PartnerContactOut
from app.services.crypto_util import new_id
from app.services.partner_service import get_ecommerce_or_404, get_logistics_or_404


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _resolve_partner(db: Session, partner_id: str, partner_type: str) -> str:
    pt = partner_type.upper()
    if pt == "ECOMMERCE":
        get_ecommerce_or_404(db, partner_id)
    else:
        get_logistics_or_404(db, partner_id)
    return pt


def list_contacts(db: Session, partner_id: str, partner_type: str) -> PartnerContactListOut:
    pt = _resolve_partner(db, partner_id, partner_type)
    rows = (
        db.query(PartnerContact)
        .filter(PartnerContact.partner_id == partner_id, PartnerContact.partner_type == pt)
        .order_by(PartnerContact.is_primary.desc(), PartnerContact.name)
        .all()
    )
    return PartnerContactListOut(
        partner_id=partner_id,
        partner_type=pt,
        contacts=[PartnerContactOut.model_validate(r) for r in rows],
    )


def create_contact(
    db: Session,
    partner_id: str,
    partner_type: str,
    body: PartnerContactCreateIn,
) -> PartnerContactOut:
    pt = _resolve_partner(db, partner_id, partner_type)
    now = _utcnow()
    row = PartnerContact(
        id=new_id(),
        partner_id=partner_id,
        partner_type=pt,
        contact_type=body.contact_type,
        name=body.name,
        email=body.email,
        phone=body.phone,
        is_primary=body.is_primary,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return PartnerContactOut.model_validate(row)
