from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models.capability import CapabilityProfile, CapabilityProfileSnapshot
from app.schemas.common import ListOut, ProfileDetailOut, ProfileIn, ProfileOut

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("", response_model=ListOut)
def list_profiles(active_only: bool = False, db: Session = Depends(get_db)) -> ListOut:
    q = db.query(CapabilityProfile)
    if active_only:
        q = q.filter(CapabilityProfile.is_active.is_(True))
    items = q.order_by(CapabilityProfile.profile_code).all()
    return ListOut(items=[ProfileOut.model_validate(i) for i in items], total=len(items))


@router.post("", response_model=ProfileOut, status_code=status.HTTP_201_CREATED)
def create_profile(body: ProfileIn, db: Session = Depends(get_db)) -> ProfileOut:
    row = CapabilityProfile(**body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return ProfileOut.model_validate(row)


@router.get("/{profile_id}", response_model=ProfileDetailOut)
def get_profile(profile_id: int, db: Session = Depends(get_db)) -> ProfileDetailOut:
    row = (
        db.query(CapabilityProfile)
        .options(
            joinedload(CapabilityProfile.actions),
            joinedload(CapabilityProfile.methods),
            joinedload(CapabilityProfile.constraints),
            joinedload(CapabilityProfile.targets),
            joinedload(CapabilityProfile.webhooks),
            joinedload(CapabilityProfile.api_keys),
        )
        .filter(CapabilityProfile.id == profile_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="profile_not_found")
    active_key = next((k for k in row.api_keys if k.active), None)
    wh = row.webhooks[0] if row.webhooks else None
    base = ProfileOut.model_validate(row)
    return ProfileDetailOut(
        **base.model_dump(),
        actions=[{"id": a.id, "action_code": a.action_code, "label": a.label, "is_active": a.is_active} for a in row.actions],
        methods=[{"id": m.id, "payment_method_id": m.payment_method_id, "is_default": m.is_default} for m in row.methods],
        constraints=[{"id": c.id, "code": c.code} for c in row.constraints],
        targets=[{"id": t.id, "target_type": t.target_type, "target_key": t.target_key} for t in row.targets],
        webhook={"id": wh.id, "url": wh.url, "active": wh.active} if wh else None,
        api_key_prefix=active_key.key_prefix if active_key else None,
    )


@router.patch("/{profile_id}", response_model=ProfileOut)
def update_profile(profile_id: int, body: ProfileIn, db: Session = Depends(get_db)) -> ProfileOut:
    row = db.get(CapabilityProfile, profile_id)
    if not row:
        raise HTTPException(status_code=404, detail="profile_not_found")
    for k, v in body.model_dump().items():
        setattr(row, k, v)
    db.commit()
    db.refresh(row)
    return ProfileOut.model_validate(row)


@router.post("/{profile_id}/snapshots", status_code=status.HTTP_201_CREATED)
def create_snapshot(profile_id: int, created_by: str | None = None, db: Session = Depends(get_db)):
    row = db.get(CapabilityProfile, profile_id)
    if not row:
        raise HTTPException(status_code=404, detail="profile_not_found")
    last = (
        db.query(CapabilityProfileSnapshot)
        .filter(CapabilityProfileSnapshot.profile_id == profile_id)
        .order_by(CapabilityProfileSnapshot.snapshot_version.desc())
        .first()
    )
    version = (last.snapshot_version + 1) if last else 1
    snap = CapabilityProfileSnapshot(
        profile_id=profile_id,
        snapshot_version=version,
        snapshot_json={
            "profile_code": row.profile_code,
            "currency": row.currency,
            "priority": row.priority,
            "metadata_json": row.metadata_json,
        },
        created_by=created_by,
    )
    db.add(snap)
    db.commit()
    return {"profile_id": profile_id, "snapshot_version": version}
