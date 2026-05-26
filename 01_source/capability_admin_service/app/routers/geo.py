from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.geo import CapabilityCountry, CapabilityLockerLocation, CapabilityProvince
from app.schemas.common import CountryIn, ListOut, LockerLocationIn, ProvinceIn
from app.services.serialize import row_to_dict

router = APIRouter(prefix="/geo", tags=["geo"])


@router.get("/countries", response_model=ListOut)
def list_countries(db: Session = Depends(get_db)) -> ListOut:
    items = db.query(CapabilityCountry).order_by(CapabilityCountry.code).all()
    return ListOut(items=[row_to_dict(i) for i in items], total=len(items))


@router.post("/countries", status_code=status.HTTP_201_CREATED)
def create_country(body: CountryIn, db: Session = Depends(get_db)):
    row = CapabilityCountry(**body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row_to_dict(row)


@router.get("/provinces", response_model=ListOut)
def list_provinces(country_code: str | None = None, db: Session = Depends(get_db)) -> ListOut:
    q = db.query(CapabilityProvince)
    if country_code:
        q = q.filter(CapabilityProvince.country_code == country_code.upper())
    items = q.order_by(CapabilityProvince.code).all()
    return ListOut(items=[row_to_dict(i) for i in items], total=len(items))


@router.post("/provinces", status_code=status.HTTP_201_CREATED)
def create_province(body: ProvinceIn, db: Session = Depends(get_db)):
    row = CapabilityProvince(**body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row_to_dict(row)


@router.get("/locker-locations", response_model=ListOut)
def list_locations(province_code: str | None = None, db: Session = Depends(get_db)) -> ListOut:
    q = db.query(CapabilityLockerLocation)
    if province_code:
        q = q.filter(CapabilityLockerLocation.province_code == province_code)
    items = q.order_by(CapabilityLockerLocation.id.desc()).limit(500).all()
    return ListOut(items=[row_to_dict(i) for i in items], total=len(items))


@router.post("/locker-locations", status_code=status.HTTP_201_CREATED)
def create_location(body: LockerLocationIn, db: Session = Depends(get_db)):
    data = body.model_dump()
    row = CapabilityLockerLocation(**data)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row_to_dict(row)


@router.get("/locker-locations/{location_id}")
def get_location(location_id: int, db: Session = Depends(get_db)):
    row = db.get(CapabilityLockerLocation, location_id)
    if not row:
        raise HTTPException(status_code=404, detail="not_found")
    return row_to_dict(row)
